import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.log import tagged_logger
from app.models.conversation import ConversationHistory, ConversationRole, InputMethod
from app.models.user import User
from app.services.gio.constants import (
    EVENT_ACTION_KEYWORDS,
    EVENT_NOUN_KEYWORDS,
    EXAM_KEYWORDS,
    EXAM_NOUN_KEYWORDS,
    GRADE_KEYWORDS,
    HAIKU_MODEL,
    _DATE_RE,
    _GRADE_SCORE_RE,
    _extract_moed,
)
from app.services.gio.exam_flow import _collect_exam_fields, _missing_exam_question, _sanitise_parsed
from app.services.gio.grade_flow import _collect_grade_fields, _missing_grade_question
from app.services.gio.llm import _parse_event_text, _parse_grade_text, anthropic_client
from app.services.gio.template_handler import _simple_gio_response

logger = tagged_logger("GIO_ENGINE")


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

    # Add current message — prepend attachment context if provided, labelled so the LLM understands it
    if context:
        user_content = f"=== מידע מצרופים ===\n{context}\n=== סוף מידע ===\n\n{text}"
    else:
        user_content = text
    messages.append({"role": "user", "content": user_content})

    # Fetch user for memory checks
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    # If mid-way through collecting grade or exam fields, continue those flows
    pending_grade = (user.gio_memory or {}).get("pending_grade") if user else None
    if pending_grade:
        return await _collect_grade_fields(user_id, db, user, text, pending_grade)

    pending_exam = (user.gio_memory or {}).get("pending_exam") if user else None
    if pending_exam:
        return await _collect_exam_fields(user_id, db, user, text, pending_exam)

    system_prompt = """אתה Gio, עוזר לוגיסטי לסטודנטים באוניברסיטה הפתוחה של ישראל.
אתה מדבר עברית, קצר, ידידותי ותומך.
אם הסטודנט מזכיר מטלה, בחינה, מבחן, הגשה, שינוי תאריך, או כל אירוע אקדמי,
צור תגובה שמאשרת את ההבנה שלך בפורמט: "אז [פרטי האירוע], נכון?"
אחרת, תגיב בצורה טבעית ומועילה.
תגובה קצרה — מקסימום 2-3 משפטים.

צרופים: אם ההודעה מכילה בלוק "=== מידע מצרופים ===", השתמש/י במידע שבו כדי לענות על שאלות הסטודנט. המידע כולל פרטים על קבצים שהועלו, אירועים שחולצו ממסמכים, ציונים ועוד. סכם/י את המידע הרלוונטי בצורה ברורה.

גבולות: אתה מכיר רק את שמות הקורסים ושמות המטלות — אין לך ידע על תוכן לימודי, חומר הלימוד, שאלות מבחן, הסברים אקדמיים או פתרונות. אם הסטודנט מבקש עזרה בחומר הלימוד, הסבר בנושא אקדמי, או כל שאלה שדורשת ידע על תוכן הקורס — השב בנימוס שאינך יכול לעזור בכך, והפנה אותו לפורומים של הקורס או לצוות ההוראה."""

    try:
        response = await anthropic_client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=512,
            system=system_prompt,
            messages=messages,
        )
        reply_text = response.content[0].text

        # Detect intent: grade report > exam scheduling > generic schedule change
        is_grade_report = (
            any(kw in text for kw in GRADE_KEYWORDS)
            and bool(_GRADE_SCORE_RE.search(text))
        )
        # Exam scheduling: explicit moed (מועד א/ב/ג) is sufficient;
        # bare exam noun (בחינה/מבחן) only triggers when a date is also present.
        has_explicit_moed = any(kw in text for kw in EXAM_KEYWORDS)
        has_exam_noun = any(kw in text for kw in EXAM_NOUN_KEYWORDS)
        has_date = bool(_DATE_RE.search(text))
        is_exam = not is_grade_report and (has_explicit_moed or (has_exam_noun and has_date))
        # Schedule change: requires a clear action verb AND an event noun
        has_action = any(kw in text for kw in EVENT_ACTION_KEYWORDS)
        has_noun = any(kw in text for kw in EVENT_NOUN_KEYWORDS)
        update_detected = not is_exam and has_action and has_noun

        if is_grade_report:
            parsed = await _parse_grade_text(text)
            # Override moed with regex ground truth
            moed_from_text = _extract_moed(text)
            if moed_from_text:
                parsed["moed"] = moed_from_text
            missing = [f for f in ("grade", "course_name") if not parsed.get(f)]

            if missing:
                pending_g: dict = {**parsed, "missing": missing}
                if user:
                    memory = dict(user.gio_memory or {})
                    memory["pending_grade"] = pending_g
                    user.gio_memory = memory
                    flag_modified(user, "gio_memory")
                msg, buttons = _missing_grade_question(pending_g)
                return await _simple_gio_response(user_id, db, msg, buttons)

            # All fields present — confirm
            if user:
                memory = dict(user.gio_memory or {})
                memory["pending_grade"] = {**parsed, "missing": []}
                user.gio_memory = memory
                flag_modified(user, "gio_memory")

            grade_val = float(parsed["grade"])
            max_g = float(parsed.get("max_grade") or 100)
            course_display = parsed.get("course_name", "")
            moed_display = parsed.get("moed")
            title_display = parsed.get("assignment_title") or (
                f"בחינה מועד {moed_display}" if moed_display else "המטלה"
            )
            pct = grade_val / max_g * 100 if max_g else 0
            confirm_text = (
                f"אז קיבלת {grade_val}/{max_g} ({pct:.0f}%) "
                f"ב{title_display} בקורס {course_display} — רוצה שאשמור את הציון?"
            )
            buttons_grade = [
                {"label": "כן, שמור", "value": "confirm_grade"},
                {"label": "לא", "value": "cancel_grade"},
            ]
            grade_msg = ConversationHistory(
                user_id=user_id,
                role=ConversationRole.assistant,
                content=confirm_text,
                input_method=InputMethod.typed,
                buttons=json.dumps(buttons_grade),
            )
            db.add(grade_msg)
            await db.flush()
            return grade_msg

        if is_exam:
            # Parse upfront and validate required fields
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            parsed = _sanitise_parsed(await _parse_event_text(text, today), text)
            missing = [f for f in ("due_date", "course_name", "moed") if not parsed.get(f)]

            if missing:
                pending: dict = {**parsed, "missing": missing}
                if user:
                    memory = dict(user.gio_memory or {})
                    memory["pending_exam"] = pending
                    user.gio_memory = memory
                    flag_modified(user, "gio_memory")
                msg, buttons = _missing_exam_question(pending)
                return await _simple_gio_response(user_id, db, msg, buttons)

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
