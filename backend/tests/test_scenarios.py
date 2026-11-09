"""Scenario CRUD tests (/api/scenarios/).

Covers:
- An admin creates a scenario: 201.
- A worker cannot create one: 403.
- Any authenticated user sees the scenario list.
- An admin adds steps to a scenario.
- Fetching a scenario with all its steps.
- Unknown scenario: 404.

Scenario model:
- A scenario is an inspection template; each step in it is one question.
- Only admins create or edit scenarios; workers read and fill them in.
"""

import pytest
from httpx import AsyncClient

from backend.app.models.user import User


@pytest.mark.asyncio
async def test_create_scenario_as_admin(client: AsyncClient, admin_user: User):
    """An admin creates a scenario: 201, with id, name and is_active=True."""
    response = await client.post(
        "/api/scenarios/",
        json={"name": "Test Scenario", "description": "Testing"},
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Scenario"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_scenario_as_worker_forbidden(client: AsyncClient, worker_user: User):
    """A worker trying to create a scenario: 403 Forbidden."""
    response = await client.post(
        "/api/scenarios/",
        json={"name": "Should Fail"},
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_scenarios(client: AsyncClient, admin_user: User, worker_user: User):
    """A worker sees scenarios created by an admin."""
    await client.post(
        "/api/scenarios/",
        json={"name": "Scenario A"},
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )

    response = await client.get(
        "/api/scenarios/",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(s["name"] == "Scenario A" for s in data)


@pytest.mark.asyncio
async def test_add_step_to_scenario(client: AsyncClient, admin_user: User):
    """An admin adds a step (question) to a scenario."""
    res = await client.post(
        "/api/scenarios/",
        json={"name": "With Steps"},
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    scenario_id = res.json()["id"]

    response = await client.post(
        f"/api/scenarios/{scenario_id}/steps",
        json={"step_number": 1, "question_text": "What is the status?"},
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 201
    assert response.json()["question_text"] == "What is the status?"
    assert response.json()["step_number"] == 1


@pytest.mark.asyncio
async def test_get_scenario_with_steps(client: AsyncClient, admin_user: User):
    """GET /scenarios/{id} returns the scenario with all steps, sorted by step_number."""
    headers = {"X-Dev-Telegram-Id": str(admin_user.telegram_id)}

    res = await client.post("/api/scenarios/", json={"name": "Full Scenario"}, headers=headers)
    sid = res.json()["id"]

    # Add 3 steps
    for i in range(1, 4):
        await client.post(
            f"/api/scenarios/{sid}/steps",
            json={"step_number": i, "question_text": f"Step {i}?"},
            headers=headers,
        )

    response = await client.get(f"/api/scenarios/{sid}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Full Scenario"
    assert len(data["steps"]) == 3
    assert data["steps"][0]["step_number"] == 1
    assert data["steps"][2]["step_number"] == 3


@pytest.mark.asyncio
async def test_get_nonexistent_scenario(client: AsyncClient, admin_user: User):
    """Requesting a scenario that does not exist: 404."""
    response = await client.get(
        "/api/scenarios/99999",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_step_to_nonexistent_scenario(client: AsyncClient, admin_user: User):
    """Adding a step to a scenario that does not exist: 404."""
    response = await client.post(
        "/api/scenarios/99999/steps",
        json={"step_number": 1, "question_text": "Q?"},
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 404
