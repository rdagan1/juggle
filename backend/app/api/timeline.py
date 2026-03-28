"""Deadlines timeline endpoint."""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from jose import jwt, JWTError
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.models.deadline import Deadline, DeadlineStatus, DeadlineType
from app.models.exam_sitting import ExamSitting, ExamSittingStatus
from app.models.course import Course
from app.models.user import User
from app.models.effort import EffortAggregate

router = APIRouter(prefix="/api/timeline", tags=["timeline"])
settings = get_settings()


async def _get_current_user(token: str, db: AsyncSession) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("")
async def get_timeline(
    window: int = Query(30, ge=1, le=180),
    course_id: str | None = Query(None),
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=window)

    # Fetch user's courses
    courses_result = await db.execute(
        select(Course).where(Course.user_id == user.id)
    )
    courses = {c.id: c for c in courses_result.scalars().all()}

    # Fetch deadlines with exam sittings
    course_filter = (
        [uuid.UUID(course_id)]
        if course_id and uuid.UUID(course_id) in courses
        else list(courses.keys())
    )
    dl_result = await db.execute(
        select(Deadline)
        .where(
            and_(
                Deadline.course_id.in_(course_filter),
                Deadline.due_date >= now,
                Deadline.due_date <= end,
            )
        )
        .options(selectinload(Deadline.exam_sittings))
        .order_by(Deadline.due_date)
    )
    deadlines = dl_result.scalars().all()

    items = []
    for dl in deadlines:
        course = courses.get(dl.course_id)
        estimate = None
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
                estimate = agg.mean_hours

        # Pick the confirmed sitting's moed for exam events
        moed: str | None = None
        if dl.type == DeadlineType.exam and dl.exam_sittings:
            confirmed = next(
                (s for s in dl.exam_sittings if s.status == ExamSittingStatus.confirmed),
                dl.exam_sittings[0],
            )
            moed = confirmed.moed_label

        items.append({
            "id": str(dl.id),
            "course_name": course.name if course else "Unknown",
            "course_code": course.code if course else None,
            "type": dl.type.value,
            "title": dl.title,
            "due_date": dl.due_date.isoformat(),
            "status": dl.status.value,
            "needs_review": dl.needs_review,
            "estimated_hours": estimate,
            "is_urgent": (dl.due_date - now).total_seconds() <= 72 * 3600,
            "moed": moed,
            "source": dl.source.value,
        })

    return {"items": items, "total": len(items)}


@router.delete("/{deadline_id}", status_code=204)
async def delete_deadline(
    deadline_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)
    courses_result = await db.execute(
        select(Course).where(Course.user_id == user.id)
    )
    user_course_ids = {c.id for c in courses_result.scalars().all()}

    result = await db.execute(
        select(Deadline).where(Deadline.id == uuid.UUID(deadline_id))
    )
    deadline = result.scalar_one_or_none()
    if not deadline or deadline.course_id not in user_course_ids:
        raise HTTPException(status_code=404, detail="Deadline not found")
    await db.delete(deadline)
    await db.commit()
