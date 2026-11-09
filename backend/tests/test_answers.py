"""Step answers (/api/objects/{id}/steps/{step_id}/answer).

Business rules:
- A step can be answered once: POST creates the answer, PUT edits it.
- An answer stays editable until an admin locks it; a locked answer needs an admin unlock.
- Only the object's creator, its responsible workers and admins may touch its answers.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.scenario import Scenario, ScenarioStep
from backend.app.models.user import User


def _auth(user: User) -> dict[str, str]:
    return {"X-Dev-Telegram-Id": str(user.telegram_id)}


async def _setup_object(client: AsyncClient, db: AsyncSession, worker: User) -> tuple[int, int]:
    """Create a one-step scenario and an object on it; return (object_id, step_id)."""
    scenario = Scenario(name="Answer Test", description="test")
    db.add(scenario)
    await db.flush()
    step = ScenarioStep(scenario_id=scenario.id, step_number=1, question_text="Test question?")
    db.add(step)
    await db.commit()
    await db.refresh(step)

    res = await client.post(
        "/api/objects/",
        json={"name": "Answer Obj", "scenario_id": scenario.id},
        headers=_auth(worker),
    )
    return res.json()["id"], step.id


async def _answer(client: AsyncClient, user: User, obj_id: int, step_id: int, text: str = "Original"):
    return await client.post(
        f"/api/objects/{obj_id}/steps/{step_id}/answer",
        json={"answer_text": text},
        headers=_auth(user),
    )


async def _edit(client: AsyncClient, user: User, obj_id: int, step_id: int, text: str = "Updated"):
    return await client.put(
        f"/api/objects/{obj_id}/steps/{step_id}/answer",
        json={"answer_text": text},
        headers=_auth(user),
    )


@pytest.mark.asyncio
async def test_submit_answer(client: AsyncClient, worker_user: User, db: AsyncSession):
    """A new answer is saved, attributed to its author and left unlocked."""
    obj_id, step_id = await _setup_object(client, db, worker_user)

    response = await _answer(client, worker_user, obj_id, step_id, "Everything is fine")

    assert response.status_code == 201
    data = response.json()
    assert data["answer_text"] == "Everything is fine"
    assert data["is_locked"] is False
    assert data["answered_by_id"] == worker_user.id


@pytest.mark.asyncio
async def test_duplicate_answer_rejected(client: AsyncClient, worker_user: User, db: AsyncSession):
    """A second POST on the same step conflicts; edits go through PUT."""
    obj_id, step_id = await _setup_object(client, db, worker_user)
    await _answer(client, worker_user, obj_id, step_id, "First answer")

    response = await _answer(client, worker_user, obj_id, step_id, "Second answer")

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_worker_edits_unlocked_answer(client: AsyncClient, worker_user: User, db: AsyncSession):
    obj_id, step_id = await _setup_object(client, db, worker_user)
    await _answer(client, worker_user, obj_id, step_id)

    response = await _edit(client, worker_user, obj_id, step_id)

    assert response.status_code == 200
    assert response.json()["answer_text"] == "Updated"


@pytest.mark.asyncio
async def test_update_locked_answer_forbidden(
    client: AsyncClient, admin_user: User, worker_user: User, db: AsyncSession
):
    """Once an admin locks the answer, the worker can no longer edit it."""
    obj_id, step_id = await _setup_object(client, db, worker_user)
    answer_id = (await _answer(client, worker_user, obj_id, step_id)).json()["id"]
    await client.patch(f"/api/admin/answers/{answer_id}/lock", headers=_auth(admin_user))

    response = await _edit(client, worker_user, obj_id, step_id)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_unlock_then_worker_edits(
    client: AsyncClient, admin_user: User, worker_user: User, db: AsyncSession
):
    """Full cycle: answer, admin lock, admin unlock, worker edit."""
    obj_id, step_id = await _setup_object(client, db, worker_user)
    answer_id = (await _answer(client, worker_user, obj_id, step_id)).json()["id"]
    await client.patch(f"/api/admin/answers/{answer_id}/lock", headers=_auth(admin_user))

    unlock_res = await client.patch(f"/api/admin/answers/{answer_id}/unlock", headers=_auth(admin_user))
    assert unlock_res.status_code == 200

    edit_res = await _edit(client, worker_user, obj_id, step_id)
    assert edit_res.status_code == 200
    assert edit_res.json()["answer_text"] == "Updated"


@pytest.mark.asyncio
async def test_shared_worker_can_answer(client: AsyncClient, worker_user: User, second_worker: User, db: AsyncSession):
    """A worker the object was shared with can answer; the answer is attributed to them."""
    obj_id, step_id = await _setup_object(client, db, worker_user)
    await client.post(f"/api/objects/{obj_id}/share/{second_worker.id}", headers=_auth(worker_user))

    response = await _answer(client, second_worker, obj_id, step_id, "Answer from worker 2")

    assert response.status_code == 201
    assert response.json()["answered_by_id"] == second_worker.id


@pytest.mark.asyncio
async def test_no_access_worker_cannot_answer(
    client: AsyncClient, worker_user: User, second_worker: User, db: AsyncSession
):
    obj_id, step_id = await _setup_object(client, db, worker_user)

    response = await _answer(client, second_worker, obj_id, step_id, "Should fail")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_no_access_worker_cannot_edit(
    client: AsyncClient, worker_user: User, second_worker: User, db: AsyncSession
):
    """Editing is guarded exactly like answering, even while the answer is unlocked."""
    obj_id, step_id = await _setup_object(client, db, worker_user)
    await _answer(client, worker_user, obj_id, step_id)

    response = await _edit(client, second_worker, obj_id, step_id, "Tampered")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_nonexistent_answer(client: AsyncClient, worker_user: User, db: AsyncSession):
    obj_id, step_id = await _setup_object(client, db, worker_user)

    response = await _edit(client, worker_user, obj_id, step_id, "No answer yet")

    assert response.status_code == 404
