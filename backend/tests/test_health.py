"""Health check test.

The most basic check that the application starts and responds. A failure here points
at configuration or imports.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """GET /health returns 200 and status ok, without authentication."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_production_requires_bot_token():
    """The API refuses to start in production without a bot token; staging may run without one.

    Loading the settings never fails on this, so alembic works without the token.
    """
    from backend.app.core.config import Settings

    production = Settings(_env_file=None, app_env="production", telegram_bot_token="")
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        production.check_api_runtime()
    Settings(_env_file=None, app_env="staging", telegram_bot_token="").check_api_runtime()
    Settings(_env_file=None, app_env="production", telegram_bot_token="123:abc").check_api_runtime()
