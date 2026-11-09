"""Single entry point for notifying a user: an in-app record plus a Telegram push."""

from functools import partial

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import add_after_commit
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.user import User
from backend.app.services.bot import send_telegram_notification


async def notify(
    db: AsyncSession,
    *,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    message: str,
    push_text: str,
    object_id: int | None = None,
    step_number: int | None = None,
) -> None:
    """Record a notification now and send its push only once the transaction has committed."""
    db.add(
        Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            object_id=object_id,
            step_number=step_number,
        )
    )
    await db.flush()

    recipient = await db.get(User, user_id)
    if recipient:
        add_after_commit(db, partial(send_telegram_notification, recipient.telegram_id, push_text))
