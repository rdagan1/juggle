"""Shared test fixtures."""
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.user import User

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        name="ישראל ישראלי",
        hashed_password=pwd_context.hash("password123"),
        email_verified=True,
        virtual_email="israel.israeli.123456@students.juggle.app",
        onboarding_completed=True,
        preferences={
            "forward_emails": True,
            "assignment_first_reminder_days": 7,
            "exam_first_reminder_days": 14,
            "shabbat_blackout": True,
            "grade_alert_threshold": 70.0,
        },
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    from app.api.auth import create_tokens
    import asyncio
    tokens = create_tokens(str(test_user.id))
    return tokens.access_token
