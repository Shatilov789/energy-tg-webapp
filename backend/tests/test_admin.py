"""
Тесты админ-панели (/api/admin/).

ПРОВЕРЯЕМ:
- Создание пользователя админом → 201
- Дубликат telegram_id → 409
- Список всех пользователей
- Деактивация/активация пользователя (toggle)
- Работник не может использовать админ-эндпоинты → 403
- Комментарий к ответу → 201, создает уведомление работнику
- Разблокировка ответа → 200, создает уведомление

РОЛИ:
- admin — полный доступ: видит все, управляет пользователями, комментирует, разблокирует
- worker — только свои объекты и шаги, не может управлять пользователями
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.notification import Notification, NotificationType
from backend.app.models.scenario import Scenario, ScenarioStep
from backend.app.models.user import User


# ==================== User management ====================


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, admin_user: User):
    """Админ регистрирует нового работника по telegram_id."""
    response = await client.post(
        "/api/admin/users",
        json={
            "telegram_id": 444444444,
            "first_name": "New",
            "last_name": "Worker",
            "role": "worker",
        },
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["telegram_id"] == 444444444
    assert data["role"] == "worker"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_duplicate_user(client: AsyncClient, admin_user: User):
    """Повторная регистрация того же telegram_id → 409 Conflict."""
    headers = {"X-Dev-Telegram-Id": str(admin_user.telegram_id)}
    await client.post(
        "/api/admin/users",
        json={"telegram_id": 555555555, "first_name": "Dup"},
        headers=headers,
    )
    response = await client.post(
        "/api/admin/users",
        json={"telegram_id": 555555555, "first_name": "Dup"},
        headers=headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient, admin_user: User, worker_user: User):
    """Админ видит всех зарегистрированных пользователей."""
    response = await client.get(
        "/api/admin/users",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 2  # admin + worker как минимум
    tg_ids = [u["telegram_id"] for u in users]
    assert admin_user.telegram_id in tg_ids
    assert worker_user.telegram_id in tg_ids


@pytest.mark.asyncio
async def test_toggle_active_deactivate(client: AsyncClient, admin_user: User, worker_user: User):
    """
    Деактивация пользователя: is_active True → False.
    После этого пользователь не сможет авторизоваться.
    """
    response = await client.patch(
        f"/api/admin/users/{worker_user.id}/toggle-active",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_toggle_active_reactivate(client: AsyncClient, admin_user: User, worker_user: User):
    """
    Toggle работает в обе стороны: деактивировать → активировать.
    Два вызова toggle → возвращается в исходное состояние.
    """
    headers = {"X-Dev-Telegram-Id": str(admin_user.telegram_id)}

    # Деактивировать
    await client.patch(f"/api/admin/users/{worker_user.id}/toggle-active", headers=headers)
    # Активировать обратно
    response = await client.patch(f"/api/admin/users/{worker_user.id}/toggle-active", headers=headers)
    assert response.json()["is_active"] is True


@pytest.mark.asyncio
async def test_toggle_nonexistent_user(client: AsyncClient, admin_user: User):
    """Toggle для несуществующего пользователя → 404."""
    response = await client.patch(
        "/api/admin/users/99999/toggle-active",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 404


# ==================== Access control ====================


@pytest.mark.asyncio
async def test_worker_cannot_access_admin_endpoints(client: AsyncClient, worker_user: User):
    """Работник не имеет доступа к админ-эндпоинтам → 403 на каждый."""
    headers = {"X-Dev-Telegram-Id": str(worker_user.telegram_id)}

    # GET /admin/users
    assert (await client.get("/api/admin/users", headers=headers)).status_code == 403
    # POST /admin/users
    assert (
        await client.post(
            "/api/admin/users",
            json={"telegram_id": 1, "first_name": "X"},
            headers=headers,
        )
    ).status_code == 403
    # GET /admin/objects
    assert (await client.get("/api/admin/objects", headers=headers)).status_code == 403


# ==================== Comments ====================


async def _create_answer(client: AsyncClient, db: AsyncSession, worker: User) -> tuple[int, int]:
    """Хелпер: сценарий + объект + ответ. Возвращает (answer_id, worker_id)."""
    scenario = Scenario(name="Comment Test", description="test")
    db.add(scenario)
    await db.flush()
    step = ScenarioStep(scenario_id=scenario.id, step_number=1, question_text="Q?")
    db.add(step)
    await db.commit()
    await db.refresh(step)

    worker_h = {"X-Dev-Telegram-Id": str(worker.telegram_id)}
    obj_res = await client.post(
        "/api/objects/",
        json={"name": "Comment Obj", "scenario_id": scenario.id},
        headers=worker_h,
    )
    answer_res = await client.post(
        f"/api/objects/{obj_res.json()['id']}/steps/{step.id}/answer",
        json={"answer_text": "My answer"},
        headers=worker_h,
    )
    return answer_res.json()["id"], worker.id


@pytest.mark.asyncio
async def test_admin_comment_on_answer(
    client: AsyncClient, admin_user: User, worker_user: User, db: AsyncSession
):
    """
    Админ комментирует ответ работника.
    1. Работник отвечает на шаг
    2. Админ пишет комментарий → 201
    3. Проверяем что комментарий сохранен
    """
    answer_id, _ = await _create_answer(client, db, worker_user)

    comment_res = await client.post(
        f"/api/admin/answers/{answer_id}/comment",
        json={"comment_text": "Please clarify"},
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert comment_res.status_code == 201
    assert comment_res.json()["comment_text"] == "Please clarify"
    assert comment_res.json()["admin_id"] == admin_user.id


@pytest.mark.asyncio
async def test_admin_comment_creates_notification(
    client: AsyncClient, admin_user: User, worker_user: User, db: AsyncSession
):
    """
    Когда админ комментирует — работник получает уведомление типа ADMIN_COMMENT.
    Проверяем что после комментария в БД появляется notification для работника.
    """
    answer_id, worker_id = await _create_answer(client, db, worker_user)

    await client.post(
        f"/api/admin/answers/{answer_id}/comment",
        json={"comment_text": "Need more details"},
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )

    # Проверяем уведомление в БД
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == worker_id,
            Notification.type == NotificationType.ADMIN_COMMENT,
        )
    )
    notif = result.scalar_one_or_none()
    assert notif is not None
    assert "comment" in notif.title.lower() or "comment" in notif.message.lower()


@pytest.mark.asyncio
async def test_comment_on_nonexistent_answer(client: AsyncClient, admin_user: User):
    """Комментарий к несуществующему ответу → 404."""
    response = await client.post(
        "/api/admin/answers/99999/comment",
        json={"comment_text": "Ghost comment"},
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 404


# ==================== Unlock ====================


@pytest.mark.asyncio
async def test_unlock_creates_notification(
    client: AsyncClient, admin_user: User, worker_user: User, db: AsyncSession
):
    """
    Разблокировка ответа создает уведомление STEP_UNLOCKED для работника.
    Работник узнает что можно редактировать.
    """
    answer_id, worker_id = await _create_answer(client, db, worker_user)

    await client.patch(
        f"/api/admin/answers/{answer_id}/unlock",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )

    result = await db.execute(
        select(Notification).where(
            Notification.user_id == worker_id,
            Notification.type == NotificationType.STEP_UNLOCKED,
        )
    )
    notif = result.scalar_one_or_none()
    assert notif is not None


@pytest.mark.asyncio
async def test_unlock_nonexistent_answer(client: AsyncClient, admin_user: User):
    """Разблокировка несуществующего ответа → 404."""
    response = await client.patch(
        "/api/admin/answers/99999/unlock",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 404
