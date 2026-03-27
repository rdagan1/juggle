"""Detect if a student needs study slots for upcoming deadlines."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deadline import Deadline, DeadlineStatus, DeadlineType
from app.models.study_block import StudyBlock
from app.models.effort import EffortAggregate
from app.models.course import Course


async def check_needs_study_slot(
    user_id: uuid.UUID,
    deadline_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    """Returns True if deadline needs a study slot and doesn't have one."""
    # Check if study block already exists
    sb_result = await db.execute(
        select(StudyBlock).where(
            and_(
                StudyBlock.user_id == user_id,
                StudyBlock.deadline_id == deadline_id,
            )
        )
    )
    block = sb_result.scalar_one_or_none()
    if block:
        return False

    # Check days until deadline
    dl_result = await db.execute(select(Deadline).where(Deadline.id == deadline_id))
    dl = dl_result.scalar_one_or_none()
    if not dl:
        return False

    now = datetime.now(timezone.utc)
    days_until = (dl.due_date - now).days

    # Only suggest if within 7 days
    return days_until <= 7 and dl.status == DeadlineStatus.pending


async def get_effort_estimate(course_code: str, assignment_label: str, db: AsyncSession) -> float | None:
    """Returns mean effort hours if enough samples exist."""
    result = await db.execute(
        select(EffortAggregate).where(
            and_(
                EffortAggregate.course_code == course_code,
                EffortAggregate.sample_count >= 5,
            )
        )
    )
    agg = result.scalar_one_or_none()
    return agg.mean_hours if agg else None
