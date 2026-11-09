"""Bootstrap of the administrator on a fresh database."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.user import User, UserRole
from backend.app.services.seed import ensure_configured_admin


async def _users(db: AsyncSession) -> list[User]:
    return list((await db.execute(select(User))).scalars())


@pytest.mark.asyncio
async def test_configured_admin_is_created_once(db: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "admin_telegram_id", 555)

    await ensure_configured_admin(db)
    await ensure_configured_admin(db)

    users = await _users(db)
    assert [(user.telegram_id, user.role) for user in users] == [(555, UserRole.ADMIN)]


@pytest.mark.asyncio
async def test_no_admin_without_configuration(db: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "admin_telegram_id", 0)

    await ensure_configured_admin(db)

    assert await _users(db) == []
