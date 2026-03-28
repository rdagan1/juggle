import uuid
from datetime import datetime, timezone
from typing import Final

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationHistory
from app.models.course import Course, CourseSource
from app.models.grade import Grade, GradeType, GradeSource
from app.models.manual_update_log import ManualUpdateLog
from app.services.gio.constants import _CANCEL_WORDS, _GRADE_SCORE_RE
from app.services.gio.llm import _extract_course_name, _parse_grade_text

_GRADE_FIELD_QUESTIONS: Final[dict[str, str]] = {
    "grade": "מה הציון שקיבלת?",
    "course_name": "באיזה קורס?",
}


def _missing_grade_question(pending: dict) -> tuple[str, list]:
    """Ask for the next missing grade field, one at a time in natural language."""
    missing = pending.get("missing", [])
    for field in ("grade", "course_name"):
        if field in missing:
            return _GRADE_FIELD_QUESTIONS[field], [{"label": "בטל", "value": "cancel_grade"}]
    return "משהו חסר — תוכל/י לחזור על הפרטים?", [{"label": "בטל", "value": "cancel_grade"}]


def _clear_pending_grade(user) -> None:
    memory = dict(user.gio_memory or {})
    memory.pop("pending_grade", None)
    user.gio_memory = memory
    flag_modified(user, "gio_memory")


async def _create_grade_from_pending(
    user_id: uuid.UUID,
    db: AsyncSession,
    user,
    pending: dict,
) -> ConversationHistory:
    """Create a Grade record from a fully-populated pending_grade dict."""
    from app.services.gio.template_handler import _simple_gio_response

    grade_value: float = float(pending["grade"])
    max_grade: float = float(pending.get("max_grade") or 100)
    course_name: str | None = pending.get("course_name")
    assignment_title: str | None = pending.get("assignment_title")
    moed: str | None = pending.get("moed")
    grade_type_str: str = pending.get("grade_type", "assignment")

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

    grade_type = GradeType.exam if grade_type_str == "exam" else GradeType.assignment
    title_for_record = assignment_title or (f"בחינה מועד {moed}" if moed else None)

    grade_record = Grade(
        user_id=user_id,
        course_id=course.id,
        grade=grade_value,
        max_grade=max_grade,
        grade_type=grade_type,
        source=GradeSource.manual,
        assignment_title=title_for_record,
        received_at=datetime.now(timezone.utc),
    )
    db.add(grade_record)
    await db.flush()

    db.add(ManualUpdateLog(
        user_id=user_id,
        target_type="grade",
        target_id=grade_record.id,
        field_changed="created",
        old_value="",
        new_value=f"{grade_value}/{max_grade}",
    ))

    _clear_pending_grade(user)

    pct = grade_value / max_grade * 100 if max_grade > 0 else 0
    title_display = title_for_record or "הציון"
    return await _simple_gio_response(
        user_id, db,
        f'שמרתי: {grade_value}/{max_grade} ({pct:.0f}%) ב{title_display} בקורס {course.name}. הציון מופיע בטאב הציונים.',
    )


async def _collect_grade_fields(
    user_id: uuid.UUID,
    db: AsyncSession,
    user,
    text: str,
    pending: dict,
) -> ConversationHistory:
    """Parse the user's reply to fill in missing grade fields; create when complete."""
    from app.services.gio.template_handler import _simple_gio_response

    if any(w in text.strip() for w in _CANCEL_WORDS):
        _clear_pending_grade(user)
        return await _simple_gio_response(user_id, db, "בסדר, ביטלתי את שמירת הציון.")

    retries = pending.get("_retries", 0)
    if retries >= 3:
        _clear_pending_grade(user)
        return await _simple_gio_response(
            user_id, db,
            "לא הצלחתי לקבל את כל הפרטים. ביטלתי — תוכל/י לנסות שוב.",
        )

    parsed = await _parse_grade_text(text)
    missing_before = set(pending.get("missing", []))
    updated = dict(pending)

    # Always overwrite with newly parsed values so corrections take effect
    for field in ("grade", "max_grade", "course_name", "assignment_title", "moed", "grade_type"):
        if parsed.get(field) is not None:
            updated[field] = parsed[field]

    # Regex fallback for numeric grade
    if not updated.get("grade"):
        score_match = _GRADE_SCORE_RE.search(text)
        if score_match:
            val = float(score_match.group(1))
            if 0 <= val <= 120:
                updated["grade"] = val

    # LLM fallback for course name
    if not updated.get("course_name"):
        updated["course_name"] = await _extract_course_name(text)

    still_missing = [f for f in ("grade", "course_name") if not updated.get(f)]
    updated["missing"] = still_missing
    updated["_retries"] = retries + 1 if set(still_missing) == missing_before else 0

    memory = dict(user.gio_memory or {})
    memory["pending_grade"] = updated
    user.gio_memory = memory
    flag_modified(user, "gio_memory")

    if still_missing:
        msg, buttons = _missing_grade_question(updated)
        return await _simple_gio_response(user_id, db, msg, buttons)

    return await _create_grade_from_pending(user_id, db, user, updated)
