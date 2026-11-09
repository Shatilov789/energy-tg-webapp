"""Background task scheduler — reminders for unfilled steps."""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import func, select

from backend.app.core.config import settings
from backend.app.db.session import async_session, run_after_commit
from backend.app.models.answer import ObjectAnswer
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.object import Object, ObjectStatus
from backend.app.models.scenario import ScenarioStep
from backend.app.services.notifications import notify

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_unfilled_steps():
    """Find objects with unfilled steps past the reminder threshold and send notifications."""
    threshold = datetime.now(timezone.utc) - timedelta(days=settings.reminder_delay_days)

    async with async_session() as db:
        # Get in-progress objects updated before threshold
        result = await db.execute(
            select(Object).where(
                Object.status == ObjectStatus.IN_PROGRESS,
                Object.is_deleted.is_(False),
                Object.updated_at < threshold,
            )
        )
        objects = result.scalars().all()

        for obj in objects:
            # Count total steps for this scenario
            total_result = await db.execute(
                select(func.count(ScenarioStep.id)).where(ScenarioStep.scenario_id == obj.scenario_id)
            )
            total_steps = total_result.scalar() or 0

            # Count answered steps
            answered_result = await db.execute(
                select(func.count(ObjectAnswer.id)).where(
                    ObjectAnswer.object_id == obj.id,
                    ObjectAnswer.is_deleted.is_(False),
                )
            )
            answered_steps = answered_result.scalar() or 0

            if answered_steps < total_steps:
                next_step = answered_steps + 1

                # Avoid duplicate reminders: check if one already sent today
                today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                existing = await db.execute(
                    select(Notification).where(
                        Notification.user_id == obj.created_by_id,
                        Notification.type == NotificationType.REMINDER,
                        Notification.created_at >= today_start,
                        Notification.message.contains(obj.name),
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                await notify(
                    db,
                    user_id=obj.created_by_id,
                    notification_type=NotificationType.REMINDER,
                    title="Нагадування про незаповнений крок",
                    message=f"Обʼєкт '{obj.name}': крок {next_step} з {total_steps} очікує заповнення",
                    push_text=f"⏰ Обʼєкт «{obj.name}»: крок {next_step} з {total_steps} очікує заповнення",
                    object_id=obj.id,
                    step_number=next_step,
                )
                logger.info("Reminder sent: object %d step %d for user %d", obj.id, next_step, obj.created_by_id)

        await db.commit()
        await run_after_commit(db)


def start_scheduler():
    """Initialize and start the background scheduler."""
    scheduler.add_job(
        check_unfilled_steps,
        "interval",
        hours=12,
        id="check_unfilled_steps",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — checking unfilled steps every 12 hours")


def stop_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
