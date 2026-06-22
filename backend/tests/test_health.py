"""
Тест healthcheck endpoint.

Самый базовый тест — проверяет что приложение вообще запускается и отвечает.
Если этот тест падает — значит проблема в конфигурации или импортах.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """GET /health — должен вернуть 200 и статус ok. Не требует авторизации."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
