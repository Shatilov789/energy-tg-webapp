"""Object CRUD tests (/api/objects/).

Covers:
- A worker creates an object: 201, status in_progress.
- A worker sees only their own objects, plus shared ones.
- Object detail with answers.
- Sharing an object with another worker; sharing again is a 409.
- A worker without access: 403.
- An admin can open any object.
- Unknown object: 404.

Object model:
- An object is one concrete inspection, tied to a scenario that defines its steps.
- The creator is automatically added to object_workers.
- It can be shared with other workers; answers show who filled in what.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.scenario import Scenario, ScenarioStep
from backend.app.models.user import User


async def _create_scenario_with_steps(db: AsyncSession, num_steps: int = 3) -> Scenario:
    """Helper: create a scenario with N steps directly in the database, independent of the scenario API."""
    scenario = Scenario(name="Test Scenario", description="For testing")
    db.add(scenario)
    await db.flush()
    for i in range(1, num_steps + 1):
        db.add(ScenarioStep(scenario_id=scenario.id, step_number=i, question_text=f"Question {i}?"))
    await db.commit()
    await db.refresh(scenario)
    return scenario


@pytest.mark.asyncio
async def test_create_object(client: AsyncClient, worker_user: User, db: AsyncSession):
    """A worker creates an inspection object and gets it back with status in_progress."""
    scenario = await _create_scenario_with_steps(db)

    response = await client.post(
        "/api/objects/",
        json={"name": "ПС-1", "comment": "Test object", "scenario_id": scenario.id},
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "ПС-1"
    assert data["comment"] == "Test object"
    assert data["status"] == "in_progress"
    assert data["created_by_id"] == worker_user.id


@pytest.mark.asyncio
async def test_list_my_objects(client: AsyncClient, worker_user: User, db: AsyncSession):
    """GET /objects/ returns only the current user's objects."""
    scenario = await _create_scenario_with_steps(db)
    headers = {"X-Dev-Telegram-Id": str(worker_user.telegram_id)}

    await client.post("/api/objects/", json={"name": "Obj A", "scenario_id": scenario.id}, headers=headers)
    await client.post("/api/objects/", json={"name": "Obj B", "scenario_id": scenario.id}, headers=headers)

    response = await client.get("/api/objects/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_object_detail(client: AsyncClient, worker_user: User, db: AsyncSession):
    """GET /objects/{id} returns the object with its nested scenario and answers."""
    scenario = await _create_scenario_with_steps(db)
    headers = {"X-Dev-Telegram-Id": str(worker_user.telegram_id)}

    res = await client.post(
        "/api/objects/",
        json={"name": "Detail Obj", "scenario_id": scenario.id},
        headers=headers,
    )
    obj_id = res.json()["id"]

    response = await client.get(f"/api/objects/{obj_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Detail Obj"
    assert "answers" in data


@pytest.mark.asyncio
async def test_get_nonexistent_object(client: AsyncClient, worker_user: User):
    """Requesting an object that does not exist: 404."""
    response = await client.get(
        "/api/objects/99999",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_share_object(client: AsyncClient, worker_user: User, second_worker: User, db: AsyncSession):
    """Sharing with another worker succeeds once; repeating it is a 409 Conflict."""
    scenario = await _create_scenario_with_steps(db)

    res = await client.post(
        "/api/objects/",
        json={"name": "Shared Obj", "scenario_id": scenario.id},
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    obj_id = res.json()["id"]

    # Share
    response = await client.post(
        f"/api/objects/{obj_id}/share/{second_worker.id}",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 201

    # A repeat attempt conflicts
    response = await client.post(
        f"/api/objects/{obj_id}/share/{second_worker.id}",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_shared_worker_sees_object(client: AsyncClient, worker_user: User, second_worker: User, db: AsyncSession):
    """After sharing, the second worker sees the object in their list and can open it."""
    scenario = await _create_scenario_with_steps(db)
    w1_h = {"X-Dev-Telegram-Id": str(worker_user.telegram_id)}
    w2_h = {"X-Dev-Telegram-Id": str(second_worker.telegram_id)}

    res = await client.post(
        "/api/objects/",
        json={"name": "Shared View", "scenario_id": scenario.id},
        headers=w1_h,
    )
    obj_id = res.json()["id"]

    # Before sharing, worker 2 does not see it
    list_res = await client.get("/api/objects/", headers=w2_h)
    assert len(list_res.json()) == 0

    # Share
    await client.post(f"/api/objects/{obj_id}/share/{second_worker.id}", headers=w1_h)

    # After sharing, worker 2 sees it
    list_res = await client.get("/api/objects/", headers=w2_h)
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["name"] == "Shared View"


@pytest.mark.asyncio
async def test_object_access_forbidden_for_other_worker(
    client: AsyncClient, worker_user: User, second_worker: User, db: AsyncSession
):
    """A worker WITHOUT access cannot open someone else's object: 403."""
    scenario = await _create_scenario_with_steps(db)

    res = await client.post(
        "/api/objects/",
        json={"name": "Private Obj", "scenario_id": scenario.id},
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    obj_id = res.json()["id"]

    # The second worker tries to open it and is refused
    response = await client.get(
        f"/api/objects/{obj_id}",
        headers={"X-Dev-Telegram-Id": str(second_worker.telegram_id)},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_see_any_object(
    client: AsyncClient, admin_user: User, worker_user: User, db: AsyncSession
):
    """An admin can open any worker's object, which review and commenting rely on."""
    scenario = await _create_scenario_with_steps(db)

    res = await client.post(
        "/api/objects/",
        json={"name": "Worker Obj", "scenario_id": scenario.id},
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    obj_id = res.json()["id"]

    # An admin opens a worker's object: 200
    response = await client.get(
        f"/api/objects/{obj_id}",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Worker Obj"
