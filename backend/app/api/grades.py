"""Grades endpoint."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.grade import Grade
from app.models.course import Course
from app.models.user import User

router = APIRouter(prefix="/api/grades", tags=["grades"])
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
async def get_grades(
    course_id: str | None = Query(None),
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)

    # Fetch all grades + courses
    courses_result = await db.execute(select(Course).where(Course.user_id == user.id))
    courses = {c.id: c for c in courses_result.scalars().all()}

    grade_where = [Grade.user_id == user.id]
    if course_id:
        grade_where.append(Grade.course_id == uuid.UUID(course_id))

    grades_result = await db.execute(
        select(Grade)
        .where(*grade_where)
        .order_by(Grade.received_at.desc())
    )
    grades = grades_result.scalars().all()

    # Group by course
    by_course: dict[str, dict] = {}
    for g in grades:
        course = courses.get(g.course_id)
        cid = str(g.course_id)
        if cid not in by_course:
            by_course[cid] = {
                "course_id": cid,
                "course_name": course.name if course else "Unknown",
                "course_code": course.code if course else None,
                "grades": [],
                "average": 0.0,
            }
        by_course[cid]["grades"].append({
            "id": str(g.id),
            "assignment_title": g.assignment_title,
            "grade": g.grade,
            "max_grade": g.max_grade,
            "percentage": round(g.grade / g.max_grade * 100, 1) if g.max_grade else None,
            "grade_type": g.grade_type.value,
            "source": g.source.value,
            "received_at": g.received_at.isoformat(),
        })

    # Compute running averages
    result_list = []
    for cid, data in by_course.items():
        grades_list = data["grades"]
        if grades_list:
            avg = sum(g["percentage"] or 0 for g in grades_list) / len(grades_list)
            data["average"] = round(avg, 1)
        result_list.append(data)

    return {"courses": result_list}
