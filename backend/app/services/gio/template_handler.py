import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.log import tagged_logger
from app.models.conversation import ConversationHistory, ConversationRole, InputMethod
from app.models.course import Course, CourseSource
from app.models.deadline import Deadline, DeadlineType, DeadlineStatus, DeadlineSource
from app.models.effort import EffortRecord, EffortInputMethod, EffortRecordType
from app.models.exam_sitting import ExamSitting, ExamSittingStatus
from app.models.manual_update_log import ManualUpdateLog
from app.models.reminder_state import ReminderState
from app.models.study_block import StudyBlock
from app.models.user import User
from app.services.gcal_client import create_exam_event, create_study_event, delete_event
from app.services.gio.constants import EFFORT_BUCKETS, SNOOZE_CONFIGS
from app.services.gio.exam_flow import _clear_pending_exam, _create_exam_from_pending
from app.services.gio.grade_flow import _clear_pending_grade, _create_grade_from_pending
from app.services.gio.llm import _parse_event_text

logger = tagged_logger("GIO_ENGINE")


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

    if value == "cancel_exam":
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            _clear_pending_exam(user)
        return await _simple_gio_response(user_id, db, "בסדר, ביטלתי את הוספת הבחינה.")

    # --- CONFIRM GRADE ---
    if value == "confirm_grade":
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        pending_grade = (user.gio_memory or {}).get("pending_grade") if user else None
        if pending_grade and not pending_grade.get("missing"):
            return await _create_grade_from_pending(user_id, db, user, pending_grade)
        return await _simple_gio_response(user_id, db, "לא מצאתי פרטי ציון שמורים. אנא שלח/י שוב.")

    # --- CANCEL GRADE ---
    if value == "cancel_grade":
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            _clear_pending_grade(user)
        return await _simple_gio_response(user_id, db, "בסדר, ביטלתי את שמירת הציון.")

    # --- CONFIRM GCAL ---
    if value == "confirm_gcal":
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        pending_gcal = (user.gio_memory or {}).get("pending_gcal") if user else None
        if pending_gcal and user and user.google_calendar_token:
            sitting_id = pending_gcal.get("sitting_id")
            if sitting_id:
                sitting_result = await db.execute(
                    select(ExamSitting).where(ExamSitting.id == uuid.UUID(sitting_id))
                )
                sitting = sitting_result.scalar_one_or_none()
                if sitting:
                    try:
                        event_id = await create_exam_event(user, sitting)
                        sitting.gcal_event_id = event_id
                    except Exception:
                        logger.exception("Failed to create GCal event confirm_gcal sitting=%s", sitting_id)
        if user:
            memory = dict(user.gio_memory or {})
            memory.pop("pending_gcal", None)
            user.gio_memory = memory
            flag_modified(user, "gio_memory")
        return await _simple_gio_response(user_id, db, "הוספתי ל-Google Calendar שלך!")

    # --- DISMISS GCAL ---
    if value == "dismiss_gcal":
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            memory = dict(user.gio_memory or {})
            memory.pop("pending_gcal", None)
            user.gio_memory = memory
            flag_modified(user, "gio_memory")
        return await _simple_gio_response(user_id, db, "בסדר, לא יתווסף ליומן.")

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
