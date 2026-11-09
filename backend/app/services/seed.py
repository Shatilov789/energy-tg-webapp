"""Seed the users the application needs to start with."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.user import User, UserRole

logger = logging.getLogger(__name__)


async def seed_dev_admin(db: AsyncSession) -> None:
    """Create a dev admin user if none exists."""
    result = await db.execute(select(User).where(User.role == UserRole.ADMIN).limit(1))
    if result.scalar_one_or_none():
        return

    admin_telegram_id = settings.admin_telegram_id or 123456789
    admin = User(
        telegram_id=admin_telegram_id,
        first_name="Dev",
        last_name="Admin",
        username="dev_admin",
        role=UserRole.ADMIN,
    )
    db.add(admin)

    worker = User(
        telegram_id=987654321,
        first_name="Dev",
        last_name="Worker",
        username="dev_worker",
        role=UserRole.WORKER,
    )
    db.add(worker)

    await db.commit()
    logger.info("Seeded dev admin (tg_id=123456789) and worker (tg_id=987654321)")


async def ensure_configured_admin(db: AsyncSession) -> None:
    """Create the administrator named by ADMIN_TELEGRAM_ID, so a fresh database has someone who can log in."""
    if not settings.admin_telegram_id:
        return
    existing = await db.execute(select(User).where(User.telegram_id == settings.admin_telegram_id))
    if existing.scalar_one_or_none():
        return

    db.add(User(telegram_id=settings.admin_telegram_id, first_name="Адміністратор", role=UserRole.ADMIN))
    await db.commit()
    logger.info("Created the configured administrator")
