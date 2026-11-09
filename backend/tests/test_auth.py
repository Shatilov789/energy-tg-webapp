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

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.security import validate_telegram_init_data
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


def _signed_init_data(token: str, auth_date: int | None) -> str:
    """Build initData the way Telegram signs it."""
    fields = {"user": json.dumps({"id": 42})}
    if auth_date is not None:
        fields["auth_date"] = str(auth_date)
    check_string = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    signature = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": signature})


@pytest.fixture
def bot_token(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setattr(settings, "telegram_bot_token", "test-token")
    return "test-token"


def test_fresh_init_data_is_accepted(bot_token: str):
    assert validate_telegram_init_data(_signed_init_data(bot_token, int(time.time()))) == {"id": 42}


def test_expired_init_data_is_rejected(bot_token: str):
    stale = int(time.time()) - settings.telegram_auth_max_age_seconds - 1
    assert validate_telegram_init_data(_signed_init_data(bot_token, stale)) is None


def test_init_data_without_auth_date_is_rejected(bot_token: str):
    assert validate_telegram_init_data(_signed_init_data(bot_token, None)) is None


def test_init_data_signed_by_another_bot_is_rejected(bot_token: str):
    assert validate_telegram_init_data(_signed_init_data("other-token", int(time.time()))) is None
