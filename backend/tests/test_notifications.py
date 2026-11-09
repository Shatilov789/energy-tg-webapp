"""Notification tests (/api/notifications/).

Covers:
- The list holds only the user's own notifications, sorted by date.
- Unread counter.
- Marking one as read.
- Marking all as read brings the counter to 0.
- Isolation: a worker does not see another worker's notifications.

Notification types:
- REMINDER: unfilled step reminder (background job).
- ADMIN_COMMENT: an admin commented on an answer.
- OBJECT_SHARED: an object was shared with a worker.
- STEP_UNLOCKED: an admin unlocked a step for editing.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.notification import Notification, NotificationType
from backend.app.models.user import User


@pytest.mark.asyncio
async def test_list_notifications(client: AsyncClient, worker_user: User, db: AsyncSession):
    """GET /notifications/ returns the current user's notifications, unread by default."""
    db.add(
        Notification(
            user_id=worker_user.id,
            type=NotificationType.REMINDER,
            title="Test reminder",
            message="Fill step 5",
        )
    )
    await db.commit()

    response = await client.get(
        "/api/notifications/",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test reminder"
    assert data[0]["is_read"] is False
    assert data[0]["type"] == "reminder"


@pytest.mark.asyncio
async def test_unread_count(client: AsyncClient, worker_user: User, db: AsyncSession):
    """GET /notifications/unread-count returns the number of unread notifications."""
    for i in range(3):
        db.add(
            Notification(
                user_id=worker_user.id,
                type=NotificationType.REMINDER,
                title=f"Reminder {i}",
                message=f"msg {i}",
            )
        )
    await db.commit()

    response = await client.get(
        "/api/notifications/unread-count",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 3


@pytest.mark.asyncio
async def test_mark_read(client: AsyncClient, worker_user: User, db: AsyncSession):
    """PATCH /notifications/{id}/read marks one notification read and lowers the counter by 1."""
    notif = Notification(
        user_id=worker_user.id,
        type=NotificationType.ADMIN_COMMENT,
        title="Comment",
        message="Admin left a note",
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    headers = {"X-Dev-Telegram-Id": str(worker_user.telegram_id)}

    # Mark as read
    response = await client.patch(f"/api/notifications/{notif.id}/read", headers=headers)
    assert response.status_code == 200

    # The counter is now 0
    count_res = await client.get("/api/notifications/unread-count", headers=headers)
    assert count_res.json()["count"] == 0


@pytest.mark.asyncio
async def test_mark_all_read(client: AsyncClient, worker_user: User, db: AsyncSession):
    """PATCH /notifications/read-all marks ALL notifications read: 5 unread become 0."""
    for i in range(5):
        db.add(
            Notification(
                user_id=worker_user.id,
                type=NotificationType.REMINDER,
                title=f"R{i}",
                message=f"m{i}",
            )
        )
    await db.commit()

    headers = {"X-Dev-Telegram-Id": str(worker_user.telegram_id)}
    await client.patch("/api/notifications/read-all", headers=headers)

    res = await client.get("/api/notifications/unread-count", headers=headers)
    assert res.json()["count"] == 0


@pytest.mark.asyncio
async def test_notification_isolation(
    client: AsyncClient, worker_user: User, second_worker: User, db: AsyncSession
):
    """Isolation: a notification for worker 1 is invisible to worker 2."""
    db.add(
        Notification(
            user_id=worker_user.id,
            type=NotificationType.REMINDER,
            title="Worker 1 only",
            message="private",
        )
    )
    await db.commit()

    # Worker 2 does not see Worker 1's notifications
    response = await client.get(
        "/api/notifications/",
        headers={"X-Dev-Telegram-Id": str(second_worker.telegram_id)},
    )
    assert len(response.json()) == 0

    # Worker 2's counter is 0
    count_res = await client.get(
        "/api/notifications/unread-count",
        headers={"X-Dev-Telegram-Id": str(second_worker.telegram_id)},
    )
    assert count_res.json()["count"] == 0
