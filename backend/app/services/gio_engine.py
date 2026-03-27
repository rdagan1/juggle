"""Gio engine: routes student responses to template or LLM handlers."""
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Final

from anthropic import AsyncAnthropic
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.infra.log import tagged_logger
from app.models.conversation import ConversationHistory, ConversationRole, InputMethod
from app.models.course import Course, CourseSource
from app.models.deadline import Deadline, DeadlineType, DeadlineStatus, DeadlineSource
from app.models.grade import Grade
from app.models.study_block import StudyBlock
from app.models.effort import EffortRecord, EffortInputMethod, EffortRecordType
from app.models.exam_sitting import ExamSitting, ExamSittingStatus
from app.models.reminder_state import ReminderState
from app.models.manual_update_log import ManualUpdateLog
from app.models.uploaded_document import UploadedDocument
from app.models.user import User
from app.services.gcal_client import create_exam_event, create_study_event, delete_event
from app.services.personalization import create_gio_message, render_gio_message

settings = get_settings()
anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
logger = tagged_logger("GIO_ENGINE")
HAIKU_MODEL: Final[str] = "claude-haiku-4-5-20251001"

# Snooze durations
SNOOZE_CONFIGS: Final[dict[str, timedelta]] = {
    "snooze_tomorrow": timedelta(days=1),
    "snooze_2d": timedelta(days=2),
    "snooze_1w": timedelta(days=7),
    "snooze_never": timedelta(days=365),
}

# Effort bucket midpoints (hours)
EFFORT_BUCKETS: Final[dict[str, float]] = {
    "effort_bucket_1": 0.5,   # 0-1h → 0.5
    "effort_bucket_2": 1.5,   # 1-2h → 1.5
    "effort_bucket_3": 3.0,   # 2-4h → 3.0
    "effort_bucket_4": 6.0,   # 4-8h → 6.0
    "effort_bucket_5": 12.0,  # 8h+  → 12.0
}

EVENT_KEYWORDS: Final[tuple[str, ...]] = (
    "נדחה", "הוקדם", "שונה", "עבר", "התבטל", "תאריך", "מועד",
    "בחינה", "מבחן", "הגשה", "מטלה", 'ממ"ן', 'ממ"מ', "תרגיל",
)

EXAM_KEYWORDS: Final[tuple[str, ...]] = ("בחינה", "מבחן", "מועד א", "מועד ב", "מועד ג")

KNOWN_BUTTON_VALUES = set([
    "completed", "pending", "confirm_plan", "confirm_schedule", "reschedule",
    "dismiss", "ack", "grade_ack", "grade_improve", "confirm_exam",
    "needs_time", "confirm_parse", "reject_parse", "confirm_update", "reject_update",
    "open_file", "moed_a", "moed_b", "moed_c",
    "lecture_attend", "lecture_no_attend", "schedule_recording",
    "ready", "needs_time",
    "lecture_mode_attend", "lecture_mode_recording", "lecture_mode_per_course",
    "works_yes", "works_no",
    "onboarding_complete",
] + list(SNOOZE_CONFIGS.keys()) + list(EFFORT_BUCKETS.keys()))


async def _parse_event_text(text: str, today: str) -> dict:
    """Use LLM to extract structured event data from free-form Hebrew text."""
    prompt = (
        f"You are a scheduling assistant for Hebrew university students.\n"
        f"Parse the following Hebrew text and extract event information.\n\n"
        f"Return ONLY valid JSON (no other text):\n"
        f'{{"action": "create or update or delete", "title": "event title in Hebrew", '
        f'"due_date": "YYYY-MM-DD or null", '
        f'"type": "exam or assignment or lecture or announcement", '
        f'"course_name": "course name in Hebrew or null", '
        f'"moed": "א or ב or ג or null"}}\n\n'
        f'Use action "create" for new events, "update" for rescheduled/moved events, '
        f'"delete" for cancelled or removed events.\n'
        f'Set moed only for exam events; extract from text (e.g. "מועד א" → "א").\n'
        f"Always include title and course_name even for delete actions.\n"
        f"The title should NOT include the course name — keep it short (e.g. 'בחינה', 'מטלה 3').\n"
        f"Today's date: {today}\n\n"
        f"Text: {text}"
    )
    try:
        response = await anthropic_client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        logger.exception("Failed to parse event text")
    return {}


def _missing_exam_question(pending: dict) -> str:
    """Build a Hebrew question asking for whichever required exam fields are still missing."""
    missing = pending.get("missing", [])
    known_course = pending.get("course_name")
    known_date = pending.get("due_date")
    known_moed = pending.get("moed")

    lines: list[str] = ["כדי להוסיף את הבחינה ליומן, אני צריך עוד כמה פרטים:"]
    if "course_name" in missing:
        lines.append("• שם הקורס")
    if "due_date" in missing:
        lines.append("• תאריך הבחינה")
    if "moed" in missing:
        lines.append("• מועד (א / ב / ג)")

    known_parts: list[str] = []
    if known_course:
        known_parts.append(f"קורס: {known_course}")
    if known_date:
        known_parts.append(f"תאריך: {known_date}")
    if known_moed:
        known_parts.append(f"מועד {known_moed}")

    if known_parts:
        lines.append(f"\n(כבר יש לי: {', '.join(known_parts)})")

    return "\n".join(lines)


async def _create_exam_from_pending(
    user_id: uuid.UUID,
    db: AsyncSession,
    user,
    pending: dict,
) -> ConversationHistory:
    """Create Deadline + ExamSitting from a fully-populated pending_exam dict."""
    from app.models.exam_sitting import ExamSitting, ExamSittingStatus

    title: str = pending.get("title") or "בחינה"
    course_name: str | None = pending.get("course_name")
    due_date_str: str = pending["due_date"]
    moed: str = pending["moed"]

    due_date = datetime.fromisoformat(due_date_str).replace(tzinfo=timezone.utc)

    # Resolve course
    course: Course | None = None
    if course_name:
        courses_result = await db.execute(select(Course).where(Course.user_id == user_id))
        for c in courses_result.scalars().all():
            if course_name.lower() in c.name.lower() or (c.code and course_name in c.code):
                course = c
                break

    if not course:
        course = Course(user_id=user_id, name=course_name or "כללי", source=CourseSource.manual)
        db.add(course)
        await db.flush()

    deadline_id = uuid.uuid4()
    dl = Deadline(
        id=deadline_id,
        course_id=course.id,
        type=DeadlineType.exam,
        title=title,
        due_date=due_date,
        source=DeadlineSource.manual,
        needs_review=False,
    )
    db.add(dl)
    await db.flush()

    sitting = ExamSitting(
        deadline_id=deadline_id,
        moed_label=moed,
        sitting_date=due_date,
        status=ExamSittingStatus.confirmed,
    )
    db.add(sitting)

    # GCal
    if user and user.google_calendar_token:
        try:
            event_id = await create_exam_event(user, sitting)
            sitting.gcal_event_id = event_id
        except Exception:
            logger.exception("Failed to create GCal event for manual exam")

    db.add(ManualUpdateLog(
        user_id=user_id,
        target_type="deadline",
        target_id=deadline_id,
        field_changed="created",
        old_value="",
        new_value=title,
    ))

    # Clear pending
    memory = dict(user.gio_memory or {})
    memory.pop("pending_exam", None)
    user.gio_memory = memory
    flag_modified(user, "gio_memory")

    display_date = due_date.strftime("%-d/%-m/%Y")
    return await _simple_gio_response(
        user_id, db,
        f'הוספתי את "{title}" מועד {moed} ב-{display_date} ללוח הזמנים שלך.',
    )


_MOED_RE: Final = re.compile(r'מועד\s*([אבג])|([אבג])', re.UNICODE)


def _extract_moed(text: str) -> str | None:
    m = _MOED_RE.search(text)
    return (m.group(1) or m.group(2)) if m else None


async def _extract_course_name(text: str) -> str | None:
    """Use LLM to extract just the course name from a short Hebrew reply."""
    prompt = (
        "You are a university course name extractor.\n"
        "The student was asked for a course name and replied in Hebrew.\n"
        "Extract the course name from their reply and return ONLY the course name — nothing else.\n"
        "If you cannot identify a course name, return the single word: null\n\n"
        f"Reply: {text}"
    )
    try:
        response = await anthropic_client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=64,
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.content[0].text.strip()
        return None if result.lower() == "null" else result
    except Exception:
        logger.exception("Failed to extract course name")
        return None


async def _collect_exam_fields(
    user_id: uuid.UUID,
    db: AsyncSession,
    user,
    text: str,
    pending: dict,
) -> ConversationHistory:
    """Parse the user's reply to fill in missing exam fields; create when complete."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parsed = await _parse_event_text(text, today)
    missing_before = set(pending.get("missing", []))

    updated = dict(pending)

    # Merge LLM-parsed fields
    for field in ("due_date", "course_name", "moed"):
        if not updated.get(field) and parsed.get(field):
            updated[field] = parsed[field]
    if not updated.get("title") and parsed.get("title"):
        updated["title"] = parsed["title"]

    # Targeted fallbacks for fields the event-parser often misses in short replies
    if "moed" in missing_before and not updated.get("moed"):
        updated["moed"] = _extract_moed(text)

    if "course_name" in missing_before and not updated.get("course_name"):
        updated["course_name"] = await _extract_course_name(text)

    # Recalculate what's still missing
    still_missing = [f for f in ("due_date", "course_name", "moed") if not updated.get(f)]
    updated["missing"] = still_missing

    # Persist updated pending
    memory = dict(user.gio_memory or {})
    memory["pending_exam"] = updated
    user.gio_memory = memory
    flag_modified(user, "gio_memory")

    if still_missing:
        return await _simple_gio_response(user_id, db, _missing_exam_question(updated))

    return await _create_exam_from_pending(user_id, db, user, updated)


_DEADLINE_TYPE_LABELS: Final[dict[str, str]] = {
    "assignment": "מטלה",
    "exam": "בחינה",
    "lecture": "הרצאה",
    "announcement": "הודעה",
}
_DEADLINE_STATUS_LABELS: Final[dict[str, str]] = {
    "pending": "ממתין",
    "completed": "הושלם",
    "missed": "הוחמץ",
}
_PDF_STATUS_LABELS: Final[dict[str, str]] = {
    "pending": "בעיבוד",
    "parsed": "עובד בהצלחה",
    "unreadable": "לא ניתן לקריאה",
    "no_events": "לא נמצאו אירועים",
    "failed": "שגיאה בעיבוד",
}


async def _build_attachment_context(
    db: AsyncSession,
    user_id: uuid.UUID,
    attachments: list,
) -> str | None:
    """Query DB for each attachment ref and return a rich Hebrew context block."""
    if not attachments:
        return None

    parts: list[str] = []
    now = datetime.now(timezone.utc)

    for ref in attachments:
        att_type: str = ref.type
        att_id: uuid.UUID = ref.id

        if att_type == "deadline":
            result = await db.execute(
                select(Deadline)
                .join(Deadline.course)
                .options(selectinload(Deadline.course), selectinload(Deadline.exam_sittings))
                .where(Deadline.id == att_id, Course.user_id == user_id)
            )
            dl = result.scalar_one_or_none()
            if not dl:
                continue
            course = dl.course
            course_str = course.name + (f" ({course.code})" if course.code else "")
            lines = [
                f"[אירוע: {dl.title}]",
                f"קורס: {course_str}",
                f"סוג: {_DEADLINE_TYPE_LABELS.get(dl.type.value, dl.type.value)}",
                f"תאריך: {dl.due_date.strftime('%d/%m/%Y %H:%M')}",
                f"סטטוס: {_DEADLINE_STATUS_LABELS.get(dl.status.value, dl.status.value)}",
            ]
            for sitting in dl.exam_sittings:
                loc = f" — {sitting.location}" if sitting.location else ""
                lines.append(
                    f"מועד {sitting.moed_label}: {sitting.sitting_date.strftime('%d/%m/%Y %H:%M')}{loc}"
                )
            parts.append("\n".join(lines))

        elif att_type in ("grade", "course"):
            course_result = await db.execute(
                select(Course).where(Course.id == att_id, Course.user_id == user_id)
            )
            course = course_result.scalar_one_or_none()
            if not course:
                continue

            grades_result = await db.execute(
                select(Grade)
                .where(Grade.course_id == att_id, Grade.user_id == user_id)
                .order_by(Grade.received_at.desc())
                .limit(10)
            )
            grades = grades_result.scalars().all()

            lines = [f"[קורס: {course.name}]"]
            if course.code:
                lines.append(f"קוד: {course.code}")
            if course.semester:
                lines.append(f"סמסטר: {course.semester}")

            if grades:
                pcts = [g.grade / g.max_grade * 100 for g in grades if g.max_grade > 0]
                avg = sum(pcts) / len(pcts) if pcts else 0
                lines.append(f"ממוצע ציונים: {avg:.1f}%")
                lines.append("ציונים:")
                for g in grades[:6]:
                    pct = g.grade / g.max_grade * 100 if g.max_grade > 0 else 0
                    title = g.assignment_title or "ציון"
                    lines.append(
                        f"  • {title}: {g.grade}/{g.max_grade} ({pct:.0f}%) — {g.received_at.strftime('%d/%m/%Y')}"
                    )

            upcoming_result = await db.execute(
                select(Deadline)
                .where(Deadline.course_id == att_id, Deadline.due_date >= now)
                .order_by(Deadline.due_date.asc())
                .limit(5)
            )
            upcoming = upcoming_result.scalars().all()
            if upcoming:
                lines.append("אירועים קרובים:")
                for dl in upcoming:
                    type_str = _DEADLINE_TYPE_LABELS.get(dl.type.value, dl.type.value)
                    lines.append(f"  • {dl.title} ({type_str}) — {dl.due_date.strftime('%d/%m/%Y')}")

            parts.append("\n".join(lines))

        elif att_type == "pdf":
            doc_result = await db.execute(
                select(UploadedDocument)
                .options(selectinload(UploadedDocument.inferred_course))
                .where(UploadedDocument.id == att_id, UploadedDocument.user_id == user_id)
            )
            doc = doc_result.scalar_one_or_none()
            if not doc:
                continue
            lines = [f"[מסמך שהועלה: {doc.filename}]"]
            lines.append(f"סטטוס: {_PDF_STATUS_LABELS.get(doc.parse_status.value, doc.parse_status.value)}")
            if doc.inferred_course:
                lines.append(f"קורס מזוהה: {doc.inferred_course.name}")
            parts.append("\n".join(lines))

    return "\n\n".join(parts) if parts else None


async def handle_response(
    user_id: uuid.UUID,
    db: AsyncSession,
    message_id: uuid.UUID | None = None,
    value: str | None = None,
    text: str | None = None,
    input_method: str = "button",
    attachments: list | None = None,
) -> ConversationHistory:
    """Route to template or LLM handler. Returns persisted Gio response."""

    # Fetch context message if provided
    ctx_msg = None
    if message_id:
        result = await db.execute(
            select(ConversationHistory).where(ConversationHistory.id == message_id)
        )
        ctx_msg = result.scalar_one_or_none()

    # Build rich context from DB for any attached items
    context = await _build_attachment_context(db, user_id, attachments or [])

    if value and value in KNOWN_BUTTON_VALUES:
        return await template_handler(user_id, db, value, ctx_msg)
    else:
        return await llm_handler(user_id, db, text or value or "", ctx_msg, context=context)


async def _simple_gio_response(
    user_id: uuid.UUID,
    db: AsyncSession,
    text: str,
    buttons: list | None = None,
) -> ConversationHistory:
    msg = ConversationHistory(
        user_id=user_id,
        role=ConversationRole.assistant,
        content=text,
        input_method=InputMethod.unknown,
        buttons=json.dumps(buttons) if buttons else None,
    )
    db.add(msg)
    await db.flush()
    return msg


async def template_handler(
    user_id: uuid.UUID,
    db: AsyncSession,
    value: str,
    ctx_msg: ConversationHistory | None,
) -> ConversationHistory:
    """Handle known button values without LLM."""

    meta = {}
    if ctx_msg and ctx_msg.message_metadata:
        try:
            meta = json.loads(ctx_msg.message_metadata)
        except Exception:
            pass

    # --- COMPLETED ---
    if value == "completed":
        deadline_id = meta.get("deadline_id")
        if deadline_id:
            result = await db.execute(select(Deadline).where(Deadline.id == uuid.UUID(deadline_id)))
            dl = result.scalar_one_or_none()
            if dl:
                dl.status = DeadlineStatus.completed
                course_result = await db.execute(select(Course).where(Course.id == dl.course_id))
                course = course_result.scalar_one_or_none()
                course_code = course.code if course else None
                course_name = course.name if course else ""

                # Trigger effort collection
                effort_buttons = [
                    {"label": "עד שעה", "value": "effort_bucket_1"},
                    {"label": "1-2 שעות", "value": "effort_bucket_2"},
                    {"label": "2-4 שעות", "value": "effort_bucket_3"},
                    {"label": "4-8 שעות", "value": "effort_bucket_4"},
                    {"label": "8+ שעות", "value": "effort_bucket_5"},
                ]
                effort_meta = {
                    "course_code": course_code,
                    "assignment_label": dl.title,
                    "record_type": "assignment",
                }
                msg = ConversationHistory(
                    user_id=user_id,
                    role=ConversationRole.assistant,
                    content=f"מעולה! כמה שעות עבדת על {dl.title}? (עוזר לסטודנטים אחרים להתכונן)",
                    template_id="effort_collection_assignment",
                    buttons=json.dumps(effort_buttons),
                    message_metadata=json.dumps(effort_meta),
                )
                db.add(msg)
                await db.flush()
                return msg

        return await _simple_gio_response(user_id, db, "מעולה! סימנתי שסיימת.")

    # --- SNOOZE ---
    if value in SNOOZE_CONFIGS:
        delta = SNOOZE_CONFIGS[value]
        target_id = meta.get("target_id")
        target_type = meta.get("target_type", "deadline")
        if target_id:
            rs_result = await db.execute(
                select(ReminderState).where(
                    and_(
                        ReminderState.user_id == user_id,
                        ReminderState.target_id == uuid.UUID(target_id),
                    )
                )
            )
            rs = rs_result.scalar_one_or_none()
            if rs:
                rs.silenced_until = datetime.now(timezone.utc) + delta
                rs.snooze_count += 1

        labels = {
            "snooze_tomorrow": "מחר בבוקר",
            "snooze_2d": "עוד יומיים",
            "snooze_1w": "בעוד שבוע",
            "snooze_never": "לעולם לא שוב",
        }
        return await _simple_gio_response(user_id, db, f"בסדר, לא אפריע עד {labels[value]}.")

    # --- EFFORT BUCKETS ---
    if value in EFFORT_BUCKETS:
        hours = EFFORT_BUCKETS[value]
        course_code = meta.get("course_code", "")
        assignment_label = meta.get("assignment_label", "")
        record_type = meta.get("record_type", "assignment")

        # Fetch user to check opt-out
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        opt_out = user.preferences.get("effort_contribution_opt_out", False) if user else False

        if not opt_out and course_code:
            record = EffortRecord(
                course_code=course_code,
                assignment_label=assignment_label,
                hours_spent=hours,
                input_method=EffortInputMethod.button,
                record_type=EffortRecordType(record_type),
            )
            db.add(record)

        return await _simple_gio_response(user_id, db, f"תודה! רשמתי {hours} שעות. הנתון עוזר לסטודנטים להתכונן.")

    # --- CONFIRM PARSE ---
    if value == "confirm_parse":
        deadline_id = meta.get("deadline_id")
        if deadline_id:
            result = await db.execute(select(Deadline).where(Deadline.id == uuid.UUID(deadline_id)))
            dl = result.scalar_one_or_none()
            if dl:
                dl.needs_review = False
        return await _simple_gio_response(user_id, db, "תודה, אישרתי את הפרטים.")

    # --- REJECT PARSE ---
    if value == "reject_parse":
        return await _simple_gio_response(user_id, db, "מה הפרטים הנכונים? אשמח לעדכן.")

    # --- CONFIRM EXAM ---
    if value == "confirm_exam":
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        pending_exam = (user.gio_memory or {}).get("pending_exam") if user else None
        if pending_exam and not pending_exam.get("missing"):
            return await _create_exam_from_pending(user_id, db, user, pending_exam)
        return await _simple_gio_response(user_id, db, "לא מצאתי פרטי בחינה שמורים. אנא שלח/י שוב.")

    # --- CONFIRM UPDATE ---
    if value == "confirm_update":
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        pending = (user.gio_memory or {}).get("pending_update") if user else None

        if pending and pending.get("needs_parsing"):
            raw_text = pending.get("raw_text", "")
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            parsed = await _parse_event_text(raw_text, today)

            action: str = parsed.get("action", "create")
            title: str = parsed.get("title") or raw_text[:80]
            due_date_str: str | None = parsed.get("due_date")
            event_type_str: str = parsed.get("type", "announcement")
            course_name: str | None = parsed.get("course_name")

            def _clear_pending() -> None:
                if user:
                    memory = dict(user.gio_memory or {})
                    memory.pop("pending_update", None)
                    user.gio_memory = memory
                    flag_modified(user, "gio_memory")

            # --- DELETE ---
            if action == "delete":
                # Find the best-matching deadline for this user
                courses_result = await db.execute(select(Course).where(Course.user_id == user_id))
                user_course_ids = [c.id for c in courses_result.scalars().all()]

                matched_dl: Deadline | None = None
                if user_course_ids:
                    dl_result = await db.execute(
                        select(Deadline).where(Deadline.course_id.in_(user_course_ids))
                    )
                    title_lower = title.lower()
                    for candidate in dl_result.scalars().all():
                        if title_lower in candidate.title.lower() or candidate.title.lower() in title_lower:
                            matched_dl = candidate
                            break

                if matched_dl:
                    # Delete GCal events on related exam sittings
                    if user and user.google_calendar_token:
                        for sitting in (matched_dl.exam_sittings or []):
                            if sitting.gcal_event_id:
                                try:
                                    await delete_event(user, sitting.gcal_event_id)
                                except Exception:
                                    logger.exception("Failed to delete GCal event %s", sitting.gcal_event_id)
                    db.add(ManualUpdateLog(
                        user_id=user_id,
                        target_type="deadline",
                        target_id=matched_dl.id,
                        field_changed="deleted",
                        old_value=matched_dl.title,
                        new_value="",
                    ))
                    await db.delete(matched_dl)
                    _clear_pending()
                    return await _simple_gio_response(user_id, db, f'הסרתי את "{matched_dl.title}" מלוח הזמנים שלך.')

                _clear_pending()
                return await _simple_gio_response(user_id, db, f'לא מצאתי אירוע בשם "{title}" כדי למחוק.')

            # Parse date (needed for create / update)
            due_date: datetime | None = None
            if due_date_str:
                try:
                    due_date = datetime.fromisoformat(due_date_str).replace(tzinfo=timezone.utc)
                except ValueError:
                    pass

            # --- UPDATE ---
            if action == "update":
                courses_result = await db.execute(select(Course).where(Course.user_id == user_id))
                user_course_ids = [c.id for c in courses_result.scalars().all()]

                matched_dl = None
                if user_course_ids:
                    dl_result = await db.execute(
                        select(Deadline).where(Deadline.course_id.in_(user_course_ids))
                    )
                    title_lower = title.lower()
                    for candidate in dl_result.scalars().all():
                        if title_lower in candidate.title.lower() or candidate.title.lower() in title_lower:
                            matched_dl = candidate
                            break

                if matched_dl and due_date:
                    old_date = matched_dl.due_date.isoformat() if matched_dl.due_date else ""
                    matched_dl.due_date = due_date
                    db.add(ManualUpdateLog(
                        user_id=user_id,
                        target_type="deadline",
                        target_id=matched_dl.id,
                        field_changed="due_date",
                        old_value=old_date,
                        new_value=due_date.isoformat(),
                    ))
                    _clear_pending()
                    return await _simple_gio_response(user_id, db, f'עדכנתי את "{matched_dl.title}" לתאריך החדש.')

                if not due_date:
                    _clear_pending()
                    return await _simple_gio_response(user_id, db, "לא הצלחתי לזהות את התאריך החדש. באיזה תאריך זה?")
                _clear_pending()
                return await _simple_gio_response(user_id, db, f'לא מצאתי אירוע בשם "{title}" כדי לעדכן.')

            # --- CREATE ---
            if not due_date:
                _clear_pending()
                return await _simple_gio_response(user_id, db, "לא הצלחתי לזהות תאריך. באיזה תאריך זה?")

            # Find matching course or fall back to first course / create generic
            course: Course | None = None
            if course_name:
                courses_result = await db.execute(select(Course).where(Course.user_id == user_id))
                for c in courses_result.scalars().all():
                    if course_name.lower() in c.name.lower() or (c.code and course_name in c.code):
                        course = c
                        break

            if not course:
                fallback = await db.execute(select(Course).where(Course.user_id == user_id).limit(1))
                course = fallback.scalar_one_or_none()

            if not course:
                course = Course(
                    user_id=user_id,
                    name=course_name or "כללי",
                    source=CourseSource.manual,
                )
                db.add(course)
                await db.flush()

            type_map: dict[str, DeadlineType] = {
                "exam": DeadlineType.exam,
                "assignment": DeadlineType.assignment,
                "lecture": DeadlineType.lecture,
            }
            new_deadline_id = uuid.uuid4()
            dl = Deadline(
                id=new_deadline_id,
                course_id=course.id,
                type=type_map.get(event_type_str, DeadlineType.announcement),
                title=title,
                due_date=due_date,
                source=DeadlineSource.manual,
                needs_review=False,
            )
            db.add(dl)
            db.add(ManualUpdateLog(
                user_id=user_id,
                target_type="deadline",
                target_id=new_deadline_id,
                field_changed="created",
                old_value="",
                new_value=title,
            ))
            _clear_pending()
            return await _simple_gio_response(user_id, db, f'הוספתי את "{title}" ללוח הזמנים שלך.')

        if pending and user:
            target_type = pending.get("target_type")
            target_id = pending.get("target_id")
            field = pending.get("field")
            old_val = pending.get("old_value")
            new_val = pending.get("new_value")

            if target_type == "deadline" and target_id and field:
                result = await db.execute(select(Deadline).where(Deadline.id == uuid.UUID(target_id)))
                dl = result.scalar_one_or_none()
                if dl and field == "due_date":
                    dl.due_date = datetime.fromisoformat(new_val).replace(tzinfo=timezone.utc)

                db.add(ManualUpdateLog(
                    user_id=user_id,
                    target_type=target_type,
                    target_id=uuid.UUID(target_id),
                    field_changed=field,
                    old_value=str(old_val),
                    new_value=str(new_val),
                ))

            memory = dict(user.gio_memory or {})
            memory.pop("pending_update", None)
            user.gio_memory = memory
            flag_modified(user, "gio_memory")

        return await _simple_gio_response(user_id, db, "עדכנתי בהתאם.")

    # --- REJECT UPDATE ---
    if value == "reject_update":
        return await _simple_gio_response(user_id, db, "מה הפרטים הנכונים? תוכל/י לכתוב לי.")

    # --- MOED SELECTION ---
    if value in ("moed_a", "moed_b", "moed_c"):
        moed_map = {"moed_a": "א", "moed_b": "ב", "moed_c": "ג"}
        selected_label = moed_map[value]
        deadline_id = meta.get("deadline_id")
        if deadline_id:
            sittings_result = await db.execute(
                select(ExamSitting).where(ExamSitting.deadline_id == uuid.UUID(deadline_id))
            )
            sittings = sittings_result.scalars().all()
            for s in sittings:
                if s.moed_label == selected_label:
                    s.status = ExamSittingStatus.confirmed
                    # Create GCal event
                    try:
                        user_result = await db.execute(select(User).where(User.id == user_id))
                        user = user_result.scalar_one_or_none()
                        if user and user.google_calendar_token:
                            event_id = await create_exam_event(user, s)
                            s.gcal_event_id = event_id
                    except Exception:
                        pass
                else:
                    if s.status == ExamSittingStatus.optional:
                        pass  # keep as optional
        return await _simple_gio_response(user_id, db, f"נרשמתי למועד {selected_label}. בהצלחה!")

    # --- CONFIRM SCHEDULE ---
    if value == "confirm_schedule":
        slot = meta.get("slot")
        deadline_id = meta.get("deadline_id")
        if slot:
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            start = datetime.fromisoformat(slot["start"]).replace(tzinfo=timezone.utc)
            end = datetime.fromisoformat(slot["end"]).replace(tzinfo=timezone.utc)

            course_name = meta.get("course_name", "לימוד")
            block = StudyBlock(
                user_id=user_id,
                scheduled_start=start,
                scheduled_end=end,
            )
            if deadline_id:
                block.deadline_id = uuid.UUID(deadline_id)
            db.add(block)
            await db.flush()

            if user and user.google_calendar_token:
                try:
                    event_id = await create_study_event(user, start, end, course_name)
                    block.gcal_event_id = event_id
                except Exception:
                    pass

        return await _simple_gio_response(user_id, db, "קבעתי לך זמן לימוד ביומן!")

    # --- RESCHEDULE ---
    if value == "reschedule":
        return await _simple_gio_response(
            user_id, db,
            "מתי יותר נוח לך? אציע כמה אפשרויות אחרות.",
            buttons=[{"label": "השבוע", "value": "slots_this_week"}, {"label": "השבוע הבא", "value": "slots_next_week"}],
        )

    # --- NEEDS TIME ---
    if value == "needs_time":
        return await _simple_gio_response(
            user_id, db,
            "בוא/י נמצא זמן ביומן. מתי נוח לך?",
            buttons=[
                {"label": "מחר בבוקר", "value": "slot_tomorrow_morning"},
                {"label": "הערב", "value": "slot_tonight"},
                {"label": "בחר/י בעצמך", "value": "slot_manual"},
            ],
        )

    # --- DISMISS / ACK ---
    if value in ("dismiss", "ack", "grade_ack"):
        return await _simple_gio_response(user_id, db, "הבנתי, תודה!")

    # --- GRADE IMPROVE ---
    if value == "grade_improve":
        return await _simple_gio_response(
            user_id, db,
            "בסדר! אוכל לעזור לך להתכונן טוב יותר לפעם הבאה. רוצה לקבוע זמן לימוד?",
            buttons=[{"label": "כן, בוא/י נקבע", "value": "needs_time"}, {"label": "לא עכשיו", "value": "dismiss"}],
        )

    # --- LECTURE MODES ---
    if value == "lecture_no_attend":
        return await _simple_gio_response(
            user_id, db,
            "רוצה שאתזמן לך זמן לצפות בהקלטה?",
            buttons=[{"label": "כן", "value": "schedule_recording"}, {"label": "לא תודה", "value": "dismiss"}],
        )

    if value == "schedule_recording":
        return await _simple_gio_response(
            user_id, db,
            "מתי נוח לך לצפות בהקלטה?",
            buttons=[
                {"label": "מחר", "value": "slot_tomorrow"},
                {"label": "הסוף שבוע", "value": "slot_weekend"},
            ],
        )

    # --- ONBOARDING ---
    if value == "onboarding_complete":
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.onboarding_completed = True
        return await _simple_gio_response(
            user_id, db,
            "מעולה! כל ההגדרות נשמרו. שלח/י לי מיילים מהאוניברסיטה לכתובת הווירטואלית שלך ואני אטפל בכל השאר.",
        )

    # Fallback for unknown known values
    return await _simple_gio_response(user_id, db, "קיבלתי, תודה!")


async def llm_handler(
    user_id: uuid.UUID,
    db: AsyncSession,
    text: str,
    ctx_msg: ConversationHistory | None,
    context: str | None = None,
) -> ConversationHistory:
    """Handle free-text input via Claude Haiku."""

    # Fetch recent conversation history
    result = await db.execute(
        select(ConversationHistory)
        .where(ConversationHistory.user_id == user_id)
        .order_by(ConversationHistory.timestamp.desc())
        .limit(10)
    )
    recent = list(reversed(result.scalars().all()))

    messages = []
    for m in recent:
        messages.append({"role": m.role.value, "content": m.content})

    # Add current message — prepend attachment context if provided
    user_content = f"{context}\n\n{text}" if context else text
    messages.append({"role": "user", "content": user_content})

    # Fetch user for memory checks
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    # If we're mid-way through collecting exam fields, continue that flow
    pending_exam = (user.gio_memory or {}).get("pending_exam") if user else None
    if pending_exam:
        return await _collect_exam_fields(user_id, db, user, text, pending_exam)

    system_prompt = """אתה Gio, עוזר לימודי חכם לסטודנטים באוניברסיטה הפתוחה של ישראל.
אתה מדבר עברית, קצר, ידידותי ותומך.
אם הסטודנט מזכיר מטלה, בחינה, מבחן, הגשה, שינוי תאריך, או כל אירוע אקדמי,
צור תגובה שמאשרת את ההבנה שלך בפורמט: "אז [פרטי האירוע], נכון?"
אחרת, תגיב בצורה טבעית ומועילה.
תגובה קצרה — מקסימום 2-3 משפטים."""

    try:
        response = await anthropic_client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=512,
            system=system_prompt,
            messages=messages,
        )
        reply_text = response.content[0].text

        # Detect intent: exam event or generic update
        is_exam = any(kw in text for kw in EXAM_KEYWORDS)
        update_detected = any(kw in text for kw in EVENT_KEYWORDS)

        if is_exam:
            # Parse upfront and validate required fields
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            parsed = await _parse_event_text(text, today)
            missing = [f for f in ("due_date", "course_name", "moed") if not parsed.get(f)]

            if missing:
                pending: dict = {**parsed, "missing": missing}
                if user:
                    memory = dict(user.gio_memory or {})
                    memory["pending_exam"] = pending
                    user.gio_memory = memory
                    flag_modified(user, "gio_memory")
                return await _simple_gio_response(user_id, db, _missing_exam_question(pending))

            # All fields present — confirm with user before creating
            if user:
                memory = dict(user.gio_memory or {})
                memory["pending_exam"] = {**parsed, "missing": []}
                user.gio_memory = memory
                flag_modified(user, "gio_memory")

            moed = parsed["moed"]
            date_display = parsed["due_date"]
            course_display = parsed.get("course_name", "")
            confirm_text = f'{reply_text}\n\nרק לוודא: בחינה מועד {moed} ב-{date_display} בקורס {course_display} — נכון?'
            buttons = [
                {"label": "כן, הוסף", "value": "confirm_exam"},
                {"label": "לא, תקן", "value": "reject_update"},
            ]
            msg = ConversationHistory(
                user_id=user_id,
                role=ConversationRole.assistant,
                content=confirm_text,
                input_method=InputMethod.typed,
                buttons=json.dumps(buttons),
            )
            db.add(msg)
            await db.flush()
            return msg

        if update_detected:
            # Non-exam event update flow
            if user:
                memory = dict(user.gio_memory or {})
                memory["pending_update"] = {
                    "raw_text": text,
                    "needs_parsing": True,
                }
                user.gio_memory = memory
                flag_modified(user, "gio_memory")

            buttons = [
                {"label": "כן, נכון", "value": "confirm_update"},
                {"label": "לא, אסביר", "value": "reject_update"},
            ]
            msg = ConversationHistory(
                user_id=user_id,
                role=ConversationRole.assistant,
                content=reply_text,
                input_method=InputMethod.typed,
                buttons=json.dumps(buttons),
            )
            db.add(msg)
            await db.flush()
            return msg

    except Exception:
        logger.exception("LLM call failed user_id=%s", user_id)
        reply_text = "מצטער, לא הצלחתי לעבד את הבקשה כרגע. נסה/י שוב."

    return await _simple_gio_response(user_id, db, reply_text)
