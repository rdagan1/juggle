import uuid
from datetime import datetime, timezone
from typing import Final

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.log import tagged_logger
from app.models.conversation import ConversationHistory
from app.models.course import Course, CourseSource
from app.models.deadline import Deadline, DeadlineType, DeadlineSource
from app.models.exam_sitting import ExamSitting, ExamSittingStatus
from app.models.manual_update_log import ManualUpdateLog
from app.services.gcal_client import create_exam_event
from app.services.gio.constants import _CANCEL_WORDS, _extract_moed
from app.services.gio.llm import _extract_course_name, _parse_event_text

logger = tagged_logger("GIO_ENGINE")

_FIELD_QUESTIONS: Final[dict[str, str]] = {
    "course_name": "באיזה קורס הבחינה?",
    "due_date": "מתי הבחינה? (תאריך)",
    "moed": "איזה מועד — א, ב או ג?",
}


def _missing_exam_question(pending: dict) -> tuple[str, list]:
    """Ask for the next missing exam field, one at a time in natural language."""
    missing = pending.get("missing", [])
    # Ask only for the first missing field
    for field in ("due_date", "course_name", "moed"):
        if field in missing:
            return _FIELD_QUESTIONS[field], [{"label": "בטל", "value": "cancel_exam"}]
    # Fallback (shouldn't happen)
    return "משהו חסר — תוכל/י לחזור על הפרטים?", [{"label": "בטל", "value": "cancel_exam"}]


def _sanitise_parsed(parsed: dict, original_text: str) -> dict:
    """Override LLM-hallucinated moed with regex ground truth."""
    result = dict(parsed)
    result["moed"] = _extract_moed(original_text)
    return result


def _clear_pending_exam(user) -> None:
    memory = dict(user.gio_memory or {})
    memory.pop("pending_exam", None)
    user.gio_memory = memory
    flag_modified(user, "gio_memory")


async def _create_exam_from_pending(
    user_id: uuid.UUID,
    db: AsyncSession,
    user,
    pending: dict,
) -> ConversationHistory:
    """Create Deadline + ExamSitting from a fully-populated pending_exam dict."""
    from app.services.gio.template_handler import _simple_gio_response

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
    await db.flush()

    db.add(ManualUpdateLog(
        user_id=user_id,
        target_type="deadline",
        target_id=deadline_id,
        field_changed="created",
        old_value="",
        new_value=title,
    ))

    # Clear pending_exam
    memory = dict(user.gio_memory or {})
    memory.pop("pending_exam", None)

    display_date = due_date.strftime("%-d/%-m/%Y")
    confirm_text = f'הוספתי את "{title}" מועד {moed} ב-{display_date} ללוח הזמנים שלך.'

    has_gcal = bool(user and user.google_calendar_token)
    gcal_auto_sync = (user.preferences or {}).get("gcal_auto_sync") if user else None

    if has_gcal and gcal_auto_sync is True:
        # Auto-sync without asking
        try:
            event_id = await create_exam_event(user, sitting)
            sitting.gcal_event_id = event_id
            confirm_text += " סנכרנתי עם Google Calendar."
        except Exception:
            logger.exception("Failed to create GCal event for manual exam")
    elif has_gcal and gcal_auto_sync is None:
        # Ask the user
        memory["pending_gcal"] = {"sitting_id": str(sitting.id)}
        user.gio_memory = memory
        flag_modified(user, "gio_memory")
        return await _simple_gio_response(
            user_id, db,
            confirm_text + "\n\nרוצה שאוסיף אותה גם ל-Google Calendar שלך?",
            [
                {"label": "כן, הוסף", "value": "confirm_gcal"},
                {"label": "לא תודה", "value": "dismiss_gcal"},
            ],
        )
    # gcal_auto_sync is False, or no GCal connected — just confirm

    user.gio_memory = memory
    flag_modified(user, "gio_memory")
    return await _simple_gio_response(user_id, db, confirm_text)


async def _collect_exam_fields(
    user_id: uuid.UUID,
    db: AsyncSession,
    user,
    text: str,
    pending: dict,
) -> ConversationHistory:
    """Parse the user's reply to fill in missing exam fields; create when complete."""
    from app.services.gio.template_handler import _simple_gio_response

    # Explicit cancellation — abort the flow
    if any(w in text.strip() for w in _CANCEL_WORDS):
        _clear_pending_exam(user)
        return await _simple_gio_response(user_id, db, "בסדר, ביטלתי את הוספת הבחינה.")

    # Auto-cancel after 3 failed attempts to avoid infinite trap
    retries = pending.get("_retries", 0)
    if retries >= 3:
        _clear_pending_exam(user)
        return await _simple_gio_response(
            user_id, db,
            "לא הצלחתי לקבל את כל הפרטים. ביטלתי את ההוספה — תוכל/י לנסות שוב כשתרצה/י.",
        )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parsed = _sanitise_parsed(await _parse_event_text(text, today), text)
    missing_before = set(pending.get("missing", []))

    updated = dict(pending)

    # Merge LLM-parsed fields — always overwrite so corrections take effect
    for field in ("due_date", "course_name", "moed"):
        if parsed.get(field):
            updated[field] = parsed[field]
    if parsed.get("title"):
        updated["title"] = parsed["title"]

    # Targeted fallbacks for fields the event-parser often misses in short replies
    if not updated.get("moed"):
        updated["moed"] = _extract_moed(text)

    if not updated.get("course_name"):
        updated["course_name"] = await _extract_course_name(text)

    # Recalculate what's still missing
    still_missing = [f for f in ("due_date", "course_name", "moed") if not updated.get(f)]
    updated["missing"] = still_missing

    # Track retries — only increment if nothing was resolved
    if set(still_missing) == missing_before:
        updated["_retries"] = retries + 1
    else:
        updated["_retries"] = 0

    # Persist updated pending
    memory = dict(user.gio_memory or {})
    memory["pending_exam"] = updated
    user.gio_memory = memory
    flag_modified(user, "gio_memory")

    if still_missing:
        msg, buttons = _missing_exam_question(updated)
        return await _simple_gio_response(user_id, db, msg, buttons)

    return await _create_exam_from_pending(user_id, db, user, updated)
