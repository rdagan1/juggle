"""Tests for timeline endpoint."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_timeline_empty(client: AsyncClient, test_user, auth_token):
    response = await client.get("/api/timeline", params={"token": auth_token})
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_timeline_returns_deadlines(client: AsyncClient, test_user, auth_token, db_session):
    from app.models.course import Course
    from app.models.deadline import Deadline, DeadlineType, DeadlineStatus, DeadlineSource

    course = Course(
        user_id=test_user.id,
        code="20407",
        name="אינפי 1",
    )
    db_session.add(course)
    await db_session.flush()

    dl = Deadline(
        course_id=course.id,
        type=DeadlineType.assignment,
        title='ממ"ן 11',
        due_date=datetime.now(timezone.utc) + timedelta(days=5),
        status=DeadlineStatus.pending,
        source=DeadlineSource.email,
    )
    db_session.add(dl)
    await db_session.flush()

    response = await client.get("/api/timeline", params={"token": auth_token})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == 'ממ"ן 11'
    assert data["items"][0]["course_name"] == "אינפי 1"
    assert data["items"][0]["is_urgent"] is False


@pytest.mark.asyncio
async def test_timeline_urgent_flag(client: AsyncClient, test_user, auth_token, db_session):
    from app.models.course import Course
    from app.models.deadline import Deadline, DeadlineType, DeadlineStatus, DeadlineSource

    course = Course(user_id=test_user.id, name="קורס דחוף")
    db_session.add(course)
    await db_session.flush()

    dl = Deadline(
        course_id=course.id,
        type=DeadlineType.assignment,
        title="מטלה דחופה",
        due_date=datetime.now(timezone.utc) + timedelta(hours=24),
        status=DeadlineStatus.pending,
        source=DeadlineSource.email,
    )
    db_session.add(dl)
    await db_session.flush()

    response = await client.get("/api/timeline", params={"token": auth_token})
    assert response.status_code == 200
    items = response.json()["items"]
    assert any(i["is_urgent"] for i in items)


@pytest.mark.asyncio
async def test_timeline_excludes_past_deadlines(client: AsyncClient, test_user, auth_token, db_session):
    from app.models.course import Course
    from app.models.deadline import Deadline, DeadlineType, DeadlineStatus, DeadlineSource

    course = Course(user_id=test_user.id, name="קורס ישן")
    db_session.add(course)
    await db_session.flush()

    dl = Deadline(
        course_id=course.id,
        type=DeadlineType.assignment,
        title="מטלה ישנה",
        due_date=datetime.now(timezone.utc) - timedelta(days=2),
        status=DeadlineStatus.pending,
        source=DeadlineSource.email,
    )
    db_session.add(dl)
    await db_session.flush()

    response = await client.get("/api/timeline", params={"token": auth_token})
    assert response.status_code == 200
    assert response.json()["total"] == 0
