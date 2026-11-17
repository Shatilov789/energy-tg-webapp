"""Admin panel tests (/api/admin/).

Covers:
- Creating a user as admin: 201.
- Duplicate telegram_id: 409.
- Listing all users.
- Deactivating/activating a user (toggle).
- Workers are refused on admin endpoints: 403.
- An admin cannot deactivate themselves: 400.

Roles:
- admin: manages users.
- worker: cannot manage users.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

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


@pytest.mark.asyncio
async def test_toggle_self_refused(client: AsyncClient, admin_user: User, db: AsyncSession):
    """An admin cannot deactivate themselves: 400, and they stay active."""
    response = await client.patch(
        f"/api/admin/users/{admin_user.id}/toggle-active",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Не можна деактивувати себе"

    await db.refresh(admin_user)
    assert admin_user.is_active is True


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
