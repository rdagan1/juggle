"""Courses endpoint — returns enriched course list with upcoming events and grade averages."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.models.course import Course
from app.models.deadline import Deadline, DeadlineType, DeadlineStatus
from app.models.exam_sitting import ExamSitting, ExamSittingStatus
from app.models.grade import Grade
from app.models.user import User



router = APIRouter(prefix="/api/courses", tags=["courses"])
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
async def get_courses(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)
    now = datetime.now(timezone.utc)

    courses_result = await db.execute(
        select(Course)
        .where(Course.user_id == user.id)
        .options(
            selectinload(Course.deadlines).selectinload(Deadline.exam_sittings),
            selectinload(Course.grades),
        )
        .order_by(Course.name)
    )
    courses = courses_result.scalars().all()

    items = []
    for course in courses:
        future_deadlines = [
            d for d in course.deadlines
            if d.due_date > now and d.status == DeadlineStatus.pending
        ]
        future_deadlines.sort(key=lambda d: d.due_date)

        # Next exam
        next_exam = next((d for d in future_deadlines if d.type == DeadlineType.exam), None)
        next_exam_out = None
        if next_exam:
            confirmed_sitting = next(
                (s for s in next_exam.exam_sittings if s.status == ExamSittingStatus.confirmed),
                next((s for s in next_exam.exam_sittings), None),
            )
            next_exam_out = {
                "id": str(next_exam.id),
                "title": next_exam.title,
                "due_date": next_exam.due_date.isoformat(),
                "moed": confirmed_sitting.moed_label if confirmed_sitting else None,
            }

        # Next assignment / lecture
        next_deadline = next(
            (d for d in future_deadlines if d.type != DeadlineType.exam), None
        )
        next_deadline_out = None
        if next_deadline:
            next_deadline_out = {
                "id": str(next_deadline.id),
                "title": next_deadline.title,
                "due_date": next_deadline.due_date.isoformat(),
                "type": next_deadline.type.value,
            }

        # Grade average
        grade_avg = None
        if course.grades:
            pcts = [g.grade / g.max_grade * 100 for g in course.grades if g.max_grade]
            if pcts:
                grade_avg = round(sum(pcts) / len(pcts), 1)

        items.append({
            "id": str(course.id),
            "name": course.name,
            "code": course.code,
            "semester": course.semester,
            "pending_count": len(future_deadlines),
            "next_exam": next_exam_out,
            "next_deadline": next_deadline_out,
            "grade_average": grade_avg,
        })

    return {"courses": items}


@router.delete("/{course_id}", status_code=204)
async def delete_course(
    course_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)
    result = await db.execute(
        select(Course).where(
            Course.id == uuid.UUID(course_id),
            Course.user_id == user.id,
        )
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    await db.delete(course)
    await db.commit()
