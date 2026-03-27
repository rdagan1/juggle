"""Proactivity scheduler logic (called by Celery Beat tasks)."""
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import pytz
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deadline import Deadline, DeadlineStatus
from app.models.reminder_state import ReminderState
from app.models.user import User
from app.models.course import Course
from app.models.effort import EffortAggregate
from app.services.personalization import create_gio_message

IL_TZ = pytz.timezone("Asia/Jerusalem")
QUIET_START = 23
QUIET_END = 7

HEBREW_DAYS = {
    5: True,  # Saturday = Shabbat
}


def is_quiet_hours(now_il: datetime) -> bool:
    h = now_il.hour
    return h >= QUIET_START or h < QUIET_END


def is_shabbat(now_il: datetime) -> bool:
    return now_il.weekday() == 5  # Saturday


def should_send_reminder(
    rs: Optional[ReminderState],
    days_until: int,
    prefs: dict,
    now: datetime,
) -> bool:
    if rs:
        if rs.silenced_until and rs.silenced_until > now:
            return False
        if rs.last_sent and (now - rs.last_sent).total_seconds() < 86400:
            return False
        if rs.snooze_count >= 3 and days_until > 5:
            # Throttle to every 2 days
            if rs.last_sent and (now - rs.last_sent).total_seconds() < 2 * 86400:
                return False

    first_reminder_days = prefs.get("assignment_first_reminder_days", 7)
    cadence_days = {first_reminder_days, 3, 1, 0}
    return days_until in cadence_days


async def run_proactivity_check(user: User, db: AsyncSession):
    """Check all pending deadlines for a user and send reminders."""
    now = datetime.now(timezone.utc)
    now_il = now.astimezone(IL_TZ)
    prefs = user.preferences or {}

    if is_quiet_hours(now_il):
        return
    if prefs.get("shabbat_blackout", True) and is_shabbat(now_il):
        return

    # Fetch user's courses
    courses_result = await db.execute(select(Course).where(Course.user_id == user.id))
    courses = {c.id: c for c in courses_result.scalars().all()}

    # Fetch pending deadlines
    dl_result = await db.execute(
        select(Deadline).where(
            and_(
                Deadline.course_id.in_(courses.keys()),
                Deadline.status == DeadlineStatus.pending,
                Deadline.due_date >= now,
            )
        )
    )
    deadlines = dl_result.scalars().all()

    # Count deadlines due soon for workload line
    soon_cutoff = now + timedelta(days=5)
    soon_count = sum(1 for d in deadlines if d.due_date <= soon_cutoff)

    for dl in deadlines:
        days_until = (dl.due_date - now).days

        # Fetch reminder state
        rs_result = await db.execute(
            select(ReminderState).where(
                and_(
                    ReminderState.user_id == user.id,
                    ReminderState.target_id == dl.id,
                )
            )
        )
        rs = rs_result.scalar_one_or_none()

        if not should_send_reminder(rs, days_until, prefs, now):
            continue

        course = courses.get(dl.course_id)

        # Get effort estimate
        estimated_hours = None
        estimate_sample = None
        if course and course.code:
            agg_result = await db.execute(
                select(EffortAggregate).where(
                    and_(
                        EffortAggregate.course_code == course.code,
                        EffortAggregate.sample_count >= 5,
                    )
                )
            )
            agg = agg_result.scalar_one_or_none()
            if agg:
                estimated_hours = agg.mean_hours
                estimate_sample = agg.sample_count

        # Build context
        include_name = days_until == 0 or days_until == (dl.due_date - now).days
        ctx = {
            "name": user.name or "",
            "include_name": include_name,
            "course_name": course.name if course else "הקורס",
            "assignment_title": dl.title,
            "days_until": days_until,
            "estimated_hours": str(estimated_hours) if estimated_hours else "",
            "estimate_sample": str(estimate_sample) if estimate_sample else "",
            "other_due_soon_count": max(0, soon_count - 1),
            "last_start_days_before": (user.gio_memory or {}).get("last_start_days_before"),
        }

        # Add deadline context for button actions
        deadline_meta = json.dumps({
            "deadline_id": str(dl.id),
            "target_id": str(dl.id),
            "target_type": "deadline",
        })

        template_id = "deadline_nudge"
        if dl.type.value == "exam":
            template_id = "exam_reminder"

        msg = await create_gio_message(user.id, template_id, ctx, db)
        msg.message_metadata = deadline_meta

        # Update reminder state
        if rs:
            rs.last_sent = now
            rs.send_count += 1
        else:
            new_rs = ReminderState(
                user_id=user.id,
                target_id=dl.id,
                target_type="deadline",
                last_sent=now,
                send_count=1,
            )
            db.add(new_rs)

        # Push over WebSocket
        try:
            from app.api.chat import push_gio_message
            await push_gio_message(str(user.id), msg)
        except Exception:
            pass

    await db.flush()
