"""
Тесты авторизации (endpoint /api/auth/me).

ПРОВЕРЯЕМ:
- Админ получает свои данные с role=admin
- Работник получает свои данные с role=worker
- Без заголовка авторизации → 401
- Неизвестный telegram_id → 404
- Деактивированный пользователь → 403

КАК РАБОТАЕТ АВТОРИЗАЦИЯ В DEV-РЕЖИМЕ:
- Заголовок X-Dev-Telegram-Id содержит telegram_id пользователя
- Система ищет пользователя в БД по этому ID
- Если бот-токен не задан (dev mode) — это единственный способ авторизации
- В продакшене вместо этого проверяется Telegram initData (подпись от Telegram)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User


@pytest.mark.asyncio
async def test_get_me_as_admin(client: AsyncClient, admin_user: User):
    """Админ запрашивает /me → получает свои данные, role=admin."""
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
    """Работник запрашивает /me → получает свои данные, role=worker."""
    response = await client.get(
        "/api/auth/me",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "worker"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Запрос без заголовка авторизации → 401 Unauthorized."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_unknown_user(client: AsyncClient):
    """Запрос с telegram_id которого нет в БД → 404 Not Found."""
    response = await client.get(
        "/api/auth/me",
        headers={"X-Dev-Telegram-Id": "999999999"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_me_deactivated_user(client: AsyncClient, worker_user: User, db: AsyncSession):
    """
    Деактивированный пользователь (is_active=False) → 403 Forbidden.
    Даже если пользователь есть в БД — доступ запрещен.
    Админ деактивирует через toggle-active.
    """
    worker_user.is_active = False
    await db.commit()

    response = await client.get(
        "/api/auth/me",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 403
