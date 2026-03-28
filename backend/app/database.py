from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def celery_session():
    """Yield a fresh AsyncSession for Celery tasks.

    Each Celery task runs in its own event loop (via asyncio.new_event_loop()).
    The module-level engine is bound to a different loop, causing asyncpg
    'Future attached to a different loop' errors.  Creating a new engine here
    ensures all connections are opened inside the task's own event loop.
    """
    task_engine = create_async_engine(settings.database_url, echo=False)
    factory = async_sessionmaker(task_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        try:
            yield session
        finally:
            await task_engine.dispose()
