"""notify() records the notification immediately but pushes to Telegram only after commit."""

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.db import session as session_module
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.user import User
from backend.app.services import notifications


@pytest_asyncio.fixture
async def push(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    mock = AsyncMock()
    monkeypatch.setattr(notifications, "send_telegram_notification", mock)
    return mock


@pytest_asyncio.fixture
async def session_factory(db: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    factory = async_sessionmaker(db.bind, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(session_module, "async_session", factory)
    return factory


async def _notify(db: AsyncSession, user: User) -> None:
    await notifications.notify(
        db,
        user_id=user.id,
        notification_type=NotificationType.REMINDER,
        title="Title",
        message="Message",
        push_text="Push",
    )


async def _saved_count(factory) -> int:
    async with factory() as session:
        return len((await session.execute(select(Notification))).scalars().all())


@pytest.mark.asyncio
async def test_push_is_sent_after_commit(worker_user, push, session_factory):
    dependency = session_module.get_db()
    session = await anext(dependency)
    await _notify(session, worker_user)
    push.assert_not_awaited()

    with pytest.raises(StopAsyncIteration):
        await anext(dependency)

    push.assert_awaited_once_with(worker_user.telegram_id, "Push")
    assert await _saved_count(session_factory) == 1


@pytest.mark.asyncio
async def test_rollback_sends_no_push_and_saves_nothing(worker_user, push, session_factory):
    dependency = session_module.get_db()
    session = await anext(dependency)
    await _notify(session, worker_user)

    with pytest.raises(ValueError):
        await dependency.athrow(ValueError("request failed"))

    push.assert_not_awaited()
    assert await _saved_count(session_factory) == 0


@pytest.mark.asyncio
async def test_failing_callback_does_not_break_the_request(db: AsyncSession):
    session_module.add_after_commit(db, AsyncMock(side_effect=RuntimeError("telegram is down")))
    await session_module.run_after_commit(db)
