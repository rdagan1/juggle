"""PDF ingestion pipeline: extract → pre-filter → LLM parse → cache → store."""
import hashlib
import json
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Final

import fitz  # PyMuPDF
from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.infra.log import tagged_logger
from app.models.pdf_parse_cache import PdfParseCache
from app.models.pdf_attachment import PdfAttachment, PdfParseStatus
from app.models.deadline import Deadline, DeadlineType, DeadlineStatus, DeadlineSource
from app.models.exam_sitting import ExamSitting, ExamSittingStatus
from app.models.grade import Grade, GradeType, GradeSource
from app.models.course import Course
from app.models.conversation import ConversationHistory, ConversationRole, InputMethod

settings = get_settings()
anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
logger = tagged_logger("PDF_PIPELINE")
logger.setLevel(10)  # DEBUG — verbose page-level extraction diagnostics

# Pre-filter keywords (from PRD)
EVENT_KEYWORDS: Final[list[str]] = [
    'ממ"ן', 'ממ"מ', 'הגשה', 'תרגיל',
    'בחינה', 'מועד', 'מבחן', 'בוחן',
    r'\d{1,2}[./]\d{1,2}[./]\d{2,4}',
    r'\d{1,2} ב[א-ת]+',
    'ציון', 'ציונים',
]

HAIKU_MODEL: Final[str] = "claude-haiku-4-5-20251001"

PARSE_PROMPT = """You are parsing a Hebrew university document from the Open University of Israel.
Extract all of the following from the document text:

- assignments: [{title, course_code, due_date (ISO 8601 date string), type: "assignment"}]
- exams: [{title, course_code, moeds: [{label, date (ISO 8601 date string), location}]}]
- lectures: [{course_code, date (ISO 8601 date string), duration_minutes}]
- grades: [{assignment_title, course_code, grade (float), max_grade (float)}]

Rules:
- Tables appear as tab-separated rows — treat each row as a record; the header row identifies columns.
- If you cannot determine the year for a date, use the current academic year (assume dates without year are in the upcoming semester).
- course_code is typically a 4-5 digit number.
- Return ONLY valid JSON matching this schema, no other text.
- If nothing found, return {}.

Document text:
"""


def _table_to_text(rows: list[list]) -> str:
    """Render a 2-D table as tab-separated rows so the LLM sees the structure."""
    lines: list[str] = []
    for row in rows:
        cells = [str(c or "").strip() for c in row]
        if any(cells):
            lines.append("\t".join(cells))
    return "\n".join(lines)


def _bbox_overlaps(bx: tuple, tb: tuple) -> bool:
    """Return True if block bbox bx has meaningful overlap with table bbox tb."""
    # Compute intersection area
    ix = max(0.0, min(bx[2], tb[2]) - max(bx[0], tb[0]))
    iy = max(0.0, min(bx[3], tb[3]) - max(bx[1], tb[1]))
    intersection = ix * iy
    if intersection <= 0:
        return False
    block_area = max(1.0, (bx[2] - bx[0]) * (bx[3] - bx[1]))
    # Block is "in table" only if >50% of its area overlaps a table cell region
    return (intersection / block_area) > 0.5


def _extract_page_text(page: fitz.Page) -> str:
    """Extract text from one page.  Tables are rendered as TSV; surrounding
    text blocks that overlap a detected table are skipped to avoid duplication."""
    table_bboxes: list[tuple[float, float, float, float]] = []
    segments: list[tuple[float, str]] = []  # (y-position, text)
    tables_found = 0
    tables_with_content = 0

    # ── Tables ────────────────────────────────────────────────────────────────
    try:
        for table in page.find_tables():
            tables_found += 1
            rows = table.extract()
            if rows:
                tsv = _table_to_text(rows)
                if tsv.strip():
                    tables_with_content += 1
                    segments.append((table.bbox[1], tsv))
                    table_bboxes.append(table.bbox)
    except Exception as exc:
        logger.warning("find_tables() failed on page %d: %s", page.number, exc)

    # ── Regular text (skip anything inside a table region) ────────────────────
    blocks = page.get_text("dict").get("blocks", [])
    text_blocks = skipped_blocks = 0
    for block in blocks:
        if block.get("type") != 0:  # 0 = text block
            continue
        text_blocks += 1
        bx = block["bbox"]
        if table_bboxes and any(_bbox_overlaps(bx, tb) for tb in table_bboxes):
            skipped_blocks += 1
            continue
        for line in block.get("lines", []):
            text = " ".join(s["text"] for s in line.get("spans", [])).strip()
            if text:
                segments.append((line["bbox"][1], text))

    logger.debug(
        "Page %d — tables=%d(content=%d) text_blocks=%d skipped=%d segments=%d",
        page.number, tables_found, tables_with_content, text_blocks, skipped_blocks, len(segments),
    )

    segments.sort(key=lambda s: s[0])
    return "\n".join(text for _, text in segments)


def _ocr_page(page: fitz.Page) -> str:
    """Run Tesseract OCR on a single page and return extracted text."""
    try:
        textpage = page.get_textpage_ocr(language="heb+eng", dpi=200, full=True)
        text = page.get_text(textpage=textpage).strip()
        logger.info("OCR page %d — chars=%d", page.number, len(text))
        return text
    except Exception as exc:
        logger.warning("OCR failed on page %d: %s", page.number, exc)
        return ""


def extract_text(pdf_bytes: bytes) -> str:
    """Extract all text from the PDF with table-aware page rendering.

    Falls back to Tesseract OCR for pages that yield no selectable text
    (i.e. scanned / image-only pages).
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[str] = []
    ocr_pages = 0
    for page in doc:
        page_text = _extract_page_text(page)
        if not page_text.strip():
            page_text = _ocr_page(page)
            if page_text:
                ocr_pages += 1
        if page_text.strip():
            pages.append(page_text)
    logger.info(
        "extract_text done — total_pages=%d pages_with_text=%d ocr_pages=%d",
        doc.page_count, len(pages), ocr_pages,
    )
    doc.close()
    return "\n\n".join(pages)


def _prepare_for_llm(full_text: str) -> str:
    """Return only event-relevant pages, compressed, capped at 10 000 chars.

    Filtering to relevant pages dramatically reduces input tokens and prevents
    the LLM from wasting time on course descriptions, contact info, etc.
    """
    pages = full_text.split("\n\n")
    relevant = [p for p in pages if has_extractable_events(p)]
    if not relevant:
        relevant = pages  # fallback: use everything
    combined = "\n\n".join(relevant)
    combined = re.sub(r"\n{3,}", "\n\n", combined)  # compress blank lines
    return combined[:10_000]


def has_extractable_events(text: str) -> bool:
    for pattern in EVENT_KEYWORDS:
        if re.search(pattern, text):
            return True
    return False


async def get_cached_parse(pdf_hash: str, db: AsyncSession) -> dict | None:
    result = await db.execute(
        select(PdfParseCache).where(PdfParseCache.pdf_hash == pdf_hash)
    )
    cached = result.scalar_one_or_none()
    if cached:
        if cached.delete_at and cached.delete_at < datetime.now(timezone.utc):
            return None
        cached.hit_count += 1
        return cached.parse_result
    return None


async def store_cache(pdf_hash: str, parse_result: dict, db: AsyncSession):
    delete_at = datetime.now(timezone.utc) + timedelta(days=90)
    entry = PdfParseCache(
        pdf_hash=pdf_hash,
        parse_result=parse_result,
        parsed_at=datetime.now(timezone.utc),
        delete_at=delete_at,
    )
    db.add(entry)


async def call_llm_parse(text: str) -> dict:
    llm_input = _prepare_for_llm(text)
    logger.info("LLM parse starting — input_chars=%d", len(llm_input))
    t0 = time.monotonic()
    response = await anthropic_client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=1024,
        timeout=45.0,
        messages=[
            {"role": "user", "content": PARSE_PROMPT + llm_input}
        ],
    )
    elapsed = time.monotonic() - t0
    content = response.content[0].text.strip()
    logger.info(
        "LLM parse done — elapsed=%.1fs input_tokens=%d output_tokens=%d",
        elapsed,
        response.usage.input_tokens,
        response.usage.output_tokens,
    )
    # Extract JSON from response
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    logger.warning("LLM returned no valid JSON — raw_output=%r", content[:200])
    return {}


def _needs_review(item: dict, user_courses: list[Course]) -> bool:
    """Returns True if parse result has low confidence."""
    known_codes = {c.code for c in user_courses if c.code}
    course_code = item.get("course_code")
    if course_code and course_code not in known_codes:
        return True
    # Check for missing year in date
    due_date = item.get("due_date") or item.get("date")
    if due_date and len(str(due_date)) <= 5:  # MM-DD without year
        return True
    return False


async def get_or_create_course(
    course_code: str,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Course | None:
    if not course_code:
        return None
    result = await db.execute(
        select(Course).where(Course.user_id == user_id, Course.code == course_code)
    )
    course = result.scalar_one_or_none()
    if not course:
        course = Course(
            user_id=user_id,
            code=course_code,
            name=f"קורס {course_code}",
        )
        db.add(course)
        await db.flush()
    return course


async def store_parse_results(
    parse_result: dict,
    user_id: uuid.UUID,
    pdf_attachment_id: uuid.UUID,
    db: AsyncSession,
) -> dict:  # {assignments: int, exams: int, grades: int, lectures: int}
    """Inserts deadlines, grades, exam sittings from parsed JSON."""
    user_courses_result = await db.execute(
        select(Course).where(Course.user_id == user_id)
    )
    user_courses = list(user_courses_result.scalars().all())

    inserted = {"assignments": 0, "exams": 0, "grades": 0, "lectures": 0}

    # Assignments
    for item in parse_result.get("assignments", []):
        course = await get_or_create_course(item.get("course_code"), user_id, db)
        if not course:
            continue
        try:
            due_date = datetime.fromisoformat(item["due_date"]).replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        review = _needs_review(item, user_courses)
        dl = Deadline(
            course_id=course.id,
            type=DeadlineType.assignment,
            title=item.get("title", "מטלה"),
            due_date=due_date,
            needs_review=review,
            source=DeadlineSource.email,
            source_pdf_id=pdf_attachment_id,
        )
        db.add(dl)
        inserted["assignments"] += 1

    # Exams
    for item in parse_result.get("exams", []):
        course = await get_or_create_course(item.get("course_code"), user_id, db)
        if not course:
            continue
        exam_dl = Deadline(
            course_id=course.id,
            type=DeadlineType.exam,
            title=item.get("title", "בחינה"),
            due_date=datetime.now(timezone.utc),  # placeholder, updated by moeds
            needs_review=True,
            source=DeadlineSource.email,
            source_pdf_id=pdf_attachment_id,
        )
        db.add(exam_dl)
        await db.flush()

        for moed in item.get("moeds", []):
            try:
                moed_date = datetime.fromisoformat(moed["date"]).replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            sitting = ExamSitting(
                deadline_id=exam_dl.id,
                moed_label=moed.get("label", "א"),
                sitting_date=moed_date,
                location=moed.get("location"),
                status=ExamSittingStatus.optional,
            )
            db.add(sitting)
            if exam_dl.due_date.year == datetime.now(timezone.utc).year and moed_date < exam_dl.due_date:
                exam_dl.due_date = moed_date

        inserted["exams"] += 1

    # Lectures
    for item in parse_result.get("lectures", []):
        course = await get_or_create_course(item.get("course_code"), user_id, db)
        if not course:
            continue
        try:
            lecture_date = datetime.fromisoformat(item["date"]).replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        dl = Deadline(
            course_id=course.id,
            type=DeadlineType.lecture,
            title="הרצאה",
            due_date=lecture_date,
            source=DeadlineSource.email,
            source_pdf_id=pdf_attachment_id,
        )
        db.add(dl)
        inserted["lectures"] += 1

    # Grades
    for item in parse_result.get("grades", []):
        course = await get_or_create_course(item.get("course_code"), user_id, db)
        if not course:
            continue
        try:
            grade_val = float(item["grade"])
            max_grade = float(item.get("max_grade", 100))
        except (KeyError, ValueError):
            continue
        grade = Grade(
            user_id=user_id,
            course_id=course.id,
            grade=grade_val,
            max_grade=max_grade,
            grade_type=GradeType.assignment,
            source=GradeSource.email,
            source_pdf_id=pdf_attachment_id,
            assignment_title=item.get("assignment_title"),
            received_at=datetime.now(timezone.utc),
        )
        db.add(grade)
        inserted["grades"] += 1

    await db.flush()
    return inserted


async def run_pipeline(
    pdf_bytes: bytes,
    user_id: uuid.UUID,
    pdf_attachment_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Full PDF pipeline. Returns result summary."""
    t_start = time.monotonic()
    logger.info("Pipeline start — pdf_attachment_id=%s size_bytes=%d", pdf_attachment_id, len(pdf_bytes))

    # Step 1: Hash
    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
    logger.info("Hash computed — pdf_hash=%s", pdf_hash)

    # Step 2: Cache check
    cached = await get_cached_parse(pdf_hash, db)

    if cached:
        logger.info("Cache hit — skipping extraction and LLM")
        parse_result = cached
        cache_hit = True
    else:
        # Step 3: Extract text
        t1 = time.monotonic()
        text = extract_text(pdf_bytes)
        logger.info("Text extracted — chars=%d elapsed=%.2fs", len(text), time.monotonic() - t1)

        # Step 4: Readability check
        if len(text.strip()) < 100:
            logger.warning("Unreadable PDF — extracted only %d chars", len(text.strip()))
            result = await db.execute(
                select(PdfAttachment).where(PdfAttachment.id == pdf_attachment_id)
            )
            att = result.scalar_one_or_none()
            if att:
                att.parse_status = PdfParseStatus.unreadable
                att.raw_text_length = len(text.strip())
            return {"status": "unreadable", "pdf_hash": pdf_hash}

        # Step 5: Pre-filter
        if not has_extractable_events(text):
            logger.info("Pre-filter: no event keywords found — skipping LLM")
            result = await db.execute(
                select(PdfAttachment).where(PdfAttachment.id == pdf_attachment_id)
            )
            att = result.scalar_one_or_none()
            if att:
                att.parse_status = PdfParseStatus.no_events
                att.raw_text_length = len(text.strip())
            return {"status": "no_events", "pdf_hash": pdf_hash}

        logger.info("Pre-filter passed — proceeding to LLM")

        # Step 6: LLM parse
        try:
            parse_result = await call_llm_parse(text)
        except Exception:
            logger.exception("LLM parse failed pdf_attachment_id=%s pdf_hash=%s", pdf_attachment_id, pdf_hash)
            att_result = await db.execute(
                select(PdfAttachment).where(PdfAttachment.id == pdf_attachment_id)
            )
            att = att_result.scalar_one_or_none()
            if att:
                att.parse_status = PdfParseStatus.failed
                att.raw_text_length = len(text.strip())
            return {"status": "failed", "pdf_hash": pdf_hash}
        cache_hit = False

        # Step 7: Store in cache
        await store_cache(pdf_hash, parse_result, db)

    # Update attachment status
    att_result = await db.execute(
        select(PdfAttachment).where(PdfAttachment.id == pdf_attachment_id)
    )
    att = att_result.scalar_one_or_none()
    if att:
        att.parse_status = PdfParseStatus.cache_hit if cache_hit else PdfParseStatus.parsed
        att.pdf_hash = pdf_hash

    # Step 8: Store results
    if parse_result:
        t2 = time.monotonic()
        inserted = await store_parse_results(parse_result, user_id, pdf_attachment_id, db)
        logger.info("Results stored — %s elapsed=%.2fs", inserted, time.monotonic() - t2)
    else:
        inserted = {}
        logger.info("LLM returned empty result — nothing stored")

    logger.info(
        "Pipeline complete — status=parsed cache_hit=%s total_elapsed=%.1fs",
        cache_hit,
        time.monotonic() - t_start,
    )
    return {
        "status": "parsed",
        "cache_hit": cache_hit,
        "pdf_hash": pdf_hash,
        "inserted": inserted,
        "parse_result": parse_result,
    }
