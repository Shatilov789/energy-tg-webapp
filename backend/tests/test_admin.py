"""Admin panel tests (/api/admin/).

Covers:
- Creating a user as admin: 201.
- Duplicate telegram_id: 409.
- Listing all users.
- Deactivating/activating a user (toggle).
- Workers are refused on admin endpoints: 403.
- Commenting on an answer: 201, and the worker is notified.
- Unlocking an answer: 200, and the worker is notified.

Roles:
- admin: full access; sees everything, manages users, comments, unlocks.
- worker: only their own objects and steps; cannot manage users.
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
    """An admin registers a new worker by telegram_id."""
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
    """Registering the same telegram_id again: 409 Conflict."""
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
    """An admin sees every registered user."""
    response = await client.get(
        "/api/admin/users",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 2  # at least the admin and the worker
    tg_ids = [u["telegram_id"] for u in users]
    assert admin_user.telegram_id in tg_ids
    assert worker_user.telegram_id in tg_ids


@pytest.mark.asyncio
async def test_toggle_active_deactivate(client: AsyncClient, admin_user: User, worker_user: User):
    """Deactivation flips is_active from True to False, after which the user cannot log in."""
    response = await client.patch(
        f"/api/admin/users/{worker_user.id}/toggle-active",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_toggle_active_reactivate(client: AsyncClient, admin_user: User, worker_user: User):
    """Toggling twice returns the user to the original state."""
    headers = {"X-Dev-Telegram-Id": str(admin_user.telegram_id)}

    # Deactivate
    await client.patch(f"/api/admin/users/{worker_user.id}/toggle-active", headers=headers)
    # Activate again
    response = await client.patch(f"/api/admin/users/{worker_user.id}/toggle-active", headers=headers)
    assert response.json()["is_active"] is True


@pytest.mark.asyncio
async def test_toggle_nonexistent_user(client: AsyncClient, admin_user: User):
    """Toggling a user that does not exist: 404."""
    response = await client.patch(
        "/api/admin/users/99999/toggle-active",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 404


# ==================== Access control ====================


@pytest.mark.asyncio
async def test_worker_cannot_access_admin_endpoints(client: AsyncClient, worker_user: User):
    """A worker gets 403 on every admin endpoint."""
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
    """Helper: scenario + object + answer. Returns (answer_id, worker_id)."""
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
async def test_admin_comment_on_answer(client: AsyncClient, admin_user: User, worker_user: User, db: AsyncSession):
    """An admin comments on a worker's answer and the comment is saved."""
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
    """Commenting creates an ADMIN_COMMENT notification for the worker."""
    answer_id, worker_id = await _create_answer(client, db, worker_user)

    await client.post(
        f"/api/admin/answers/{answer_id}/comment",
        json={"comment_text": "Need more details"},
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )

    # Check the notification in the database
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
    """Commenting on an answer that does not exist: 404."""
    response = await client.post(
        "/api/admin/answers/99999/comment",
        json={"comment_text": "Ghost comment"},
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 404


# ==================== Unlock ====================


@pytest.mark.asyncio
async def test_unlock_creates_notification(client: AsyncClient, admin_user: User, worker_user: User, db: AsyncSession):
    """Unlocking creates a STEP_UNLOCKED notification, so the worker knows they can edit."""
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
    """Unlocking an answer that does not exist: 404."""
    response = await client.patch(
        "/api/admin/answers/99999/unlock",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 404
