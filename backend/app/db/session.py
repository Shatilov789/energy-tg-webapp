"""Async database session factory."""

import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_size=20,
    max_overflow=10,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

_AFTER_COMMIT_KEY = "after_commit_callbacks"


def add_after_commit(session: AsyncSession, callback: Callable[[], Awaitable[None]]) -> None:
    """Queue work that must only happen if the session's transaction commits."""
    session.info.setdefault(_AFTER_COMMIT_KEY, []).append(callback)


async def run_after_commit(session: AsyncSession) -> None:
    """Run queued callbacks. The data is already saved, so a failing callback is only logged."""
    for callback in session.info.pop(_AFTER_COMMIT_KEY, []):
        try:
            await callback()
        except Exception:
            logger.exception("After-commit callback failed")


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields an async DB session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        await run_after_commit(session)
