"""Authentication tests (/api/auth/me).

Covers:
- An admin gets their data with role=admin.
- A worker gets their data with role=worker.
- No auth header: 401.
- Unknown telegram_id: 404.
- Deactivated user: 403.

Dev-mode authentication:
- The X-Dev-Telegram-Id header carries the user's telegram_id, looked up in the database.
- Outside development the Telegram initData signature is verified instead.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User


@pytest.mark.asyncio
async def test_get_me_as_admin(client: AsyncClient, admin_user: User):
    """An admin calling /me gets their own data with role=admin."""
    response = await client.get(
        "/api/auth/me",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_id"] == admin_user.telegram_id
    assert data["role"] == "admin"
    assert data["first_name"] == "Test"


@pytest.mark.asyncio
async def test_get_me_as_worker(client: AsyncClient, worker_user: User):
    """A worker calling /me gets their own data with role=worker."""
    response = await client.get(
        "/api/auth/me",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "worker"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """A request without an auth header: 401 Unauthorized."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_unknown_user(client: AsyncClient):
    """A telegram_id missing from the database: 404 Not Found."""
    response = await client.get(
        "/api/auth/me",
        headers={"X-Dev-Telegram-Id": "999999999"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_me_deactivated_user(client: AsyncClient, worker_user: User, db: AsyncSession):
    """A user deactivated through toggle-active gets 403 even though they exist in the database."""
    worker_user.is_active = False
    await db.commit()

    response = await client.get(
        "/api/auth/me",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 403
