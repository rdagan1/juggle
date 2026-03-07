"""PDF text extraction and pre-filtering for the Juggle pipeline."""
import hashlib
import re
import uuid
from typing import Optional

import pdfplumber
import io


# ── Text extraction ───────────────────────────────────────────────────────────

def extract_pdf_text(pdf_bytes: bytes) -> dict:
    """Extract text from PDF bytes.

    Returns:
        {
            "readable": bool,       # True if text > 100 chars AND contains Hebrew
            "text": str | None,
            "page_count": int,
            "raw_text_length": int,
        }
    """
    text_parts = []
    page_count = 0

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
    except Exception:
        return {"readable": False, "text": None, "page_count": page_count, "raw_text_length": 0}

    full_text = "\n".join(text_parts)
    raw_len = len(full_text)
    readable = raw_len > 100 and _contains_hebrew(full_text)

    return {
        "readable": readable,
        "text": full_text if readable else None,
        "page_count": page_count,
        "raw_text_length": raw_len,
    }


def _contains_hebrew(text: str) -> bool:
    return bool(re.search(r"[\u05d0-\u05ea]", text))


# ── Pre-filter ────────────────────────────────────────────────────────────────

# Patterns that indicate extractable academic events
_EVENT_PATTERNS = [
    r'מ+["״]ן',           # ממ"ן / מ"ן assignments
    r'בחינה',             # exam
    r'\d{1,2}/\d{1,2}/\d{2,4}',  # DD/MM/YYYY dates
    r'\d{1,2}\s+ב(?:ינואר|פברואר|מרץ|אפריל|מאי|יוני|יולי|אוגוסט|ספטמבר|אוקטובר|נובמבר|דצמבר)',
    r'ציון',              # grade
    r'מועד\s*[א-ת]',      # exam sitting
    r'תאריך\s+הגשה',      # submission date
    r'הגשה',              # submission
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _EVENT_PATTERNS]


def has_extractable_events(text: str) -> bool:
    """Return True if text likely contains academic events worth LLM parsing."""
    return any(p.search(text) for p in _COMPILED)


# ── Cache check ───────────────────────────────────────────────────────────────

async def get_cached_parse(pdf_bytes: bytes, db) -> Optional[dict]:
    """Check pdf_parse_cache by SHA-256 hash. Increments hit_count on hit.

    Args:
        pdf_bytes: Raw PDF bytes.
        db: AsyncSession.

    Returns:
        parse_result dict if cached, else None.
    """
    from sqlalchemy import select, text

    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

    result = await db.execute(
        select(_get_cache_model()).where(_get_cache_model().pdf_hash == pdf_hash)
    )
    row = result.scalar_one_or_none()
    if row:
        await db.execute(
            text("UPDATE pdf_parse_cache SET hit_count = hit_count + 1 WHERE id = :id"),
            {"id": row.id},
        )
        await db.commit()
        return row.parse_result

    return None


def compute_pdf_hash(pdf_bytes: bytes) -> str:
    return hashlib.sha256(pdf_bytes).hexdigest()


def _get_cache_model():
    """Lazy import to avoid circular deps."""
    from app.models.cache import PdfParseCache
    return PdfParseCache
