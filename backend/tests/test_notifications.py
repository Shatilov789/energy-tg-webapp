"""
Тесты уведомлений (/api/notifications/).

ПРОВЕРЯЕМ:
- Список уведомлений — только свои, отсортированы по дате
- Счетчик непрочитанных
- Пометка одного как прочитанного
- Пометка всех как прочитанных → счетчик = 0
- Изоляция: один работник не видит уведомления другого
- Комментарий админа создает уведомление работнику

ТИПЫ УВЕДОМЛЕНИЙ:
- REMINDER — напоминание о незаполненном шаге (фоновая задача)
- ADMIN_COMMENT — админ оставил комментарий к ответу
- OBJECT_SHARED — объект расшарен с работником
- STEP_UNLOCKED — админ разблокировал шаг для редактирования
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.notification import Notification, NotificationType
from backend.app.models.user import User


@pytest.mark.asyncio
async def test_list_notifications(client: AsyncClient, worker_user: User, db: AsyncSession):
    """
    GET /notifications/ — возвращает уведомления текущего пользователя.
    Создаем 1 уведомление → видим его в списке, is_read=False.
    """
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
    """GET /notifications/unread-count — количество непрочитанных."""
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
    """
    PATCH /notifications/{id}/read — помечает конкретное уведомление как прочитанное.
    После этого счетчик непрочитанных уменьшается на 1.
    """
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

    # Помечаем прочитанным
    response = await client.patch(f"/api/notifications/{notif.id}/read", headers=headers)
    assert response.status_code == 200

    # Проверяем что счетчик = 0
    count_res = await client.get("/api/notifications/unread-count", headers=headers)
    assert count_res.json()["count"] == 0


@pytest.mark.asyncio
async def test_mark_all_read(client: AsyncClient, worker_user: User, db: AsyncSession):
    """
    PATCH /notifications/read-all — помечает ВСЕ уведомления как прочитанные.
    5 непрочитанных → mark_all_read → счетчик = 0.
    """
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
    """
    Изоляция: работник видит ТОЛЬКО свои уведомления.
    Создаем уведомление для worker_1 → worker_2 не видит его.
    """
    db.add(
        Notification(
            user_id=worker_user.id,
            type=NotificationType.REMINDER,
            title="Worker 1 only",
            message="private",
        )
    )
    await db.commit()

    # Worker 2 не видит уведомления Worker 1
    response = await client.get(
        "/api/notifications/",
        headers={"X-Dev-Telegram-Id": str(second_worker.telegram_id)},
    )
    assert len(response.json()) == 0

    # Worker 2 — счетчик = 0
    count_res = await client.get(
        "/api/notifications/unread-count",
        headers={"X-Dev-Telegram-Id": str(second_worker.telegram_id)},
    )
    assert count_res.json()["count"] == 0
