"""Deal lifecycle through the API, driven by a small purpose-built process."""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.processes.catalog import seed_process
from backend.app.processes.definition import ProcessDefinition
from backend.app.processes.registry import PROCESSES

FLOW = ProcessDefinition(
    name="Flow",
    stages=[
        ("1", "t_start", "Start", "Sales", False),
        ("2", "t_gate", "Gate", "Sales", True),
        ("3", "t_split", "Split", "Sales", False),
        ("4", "t_left", "Left", "Sales", False),
        ("5", "t_right", "Right", "Sales", False),
        ("6", "t_done", "Done", "Sales", False),
        ("7", "t_lost", "Lost", "Sales", False),
    ],
    transitions={
        "t_start": {"next": "t_gate"},
        "t_gate": {"yes": "t_split", "no": "t_lost"},
        "t_split": {"parallel": ["t_left", "t_right"]},
        "t_left": {"next": "t_done"},
        "t_right": {"next": "t_done"},
        "t_done": {"terminal": "completed"},
        "t_lost": {"terminal": "closed"},
    },
)

MIXED = ProcessDefinition(
    name="Mixed",
    stages=[
        ("1", "m_split", "Split", "Sales", False),
        ("2", "m_open", "Open", "Sales", False),
        ("3", "m_done", "Done", "Sales", False),
    ],
    transitions={
        "m_split": {"parallel": ["m_done", "m_open"]},
        "m_open": {"next": "m_done"},
        "m_done": {"terminal": "completed"},
    },
)


@pytest_asyncio.fixture
async def processes(db: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    for process in (FLOW, MIXED):
        monkeypatch.setitem(PROCESSES, process.name, process)
        await seed_process(db, process)


def _auth(user: User) -> dict[str, str]:
    return {"X-Dev-Telegram-Id": str(user.telegram_id)}


async def _create(client: AsyncClient, user: User, process_type: str = "Flow") -> dict:
    response = await client.post(
        "/api/deals/",
        json={"process_type": process_type, "client_name": "Client", "client_phone": "+380000000000"},
        headers=_auth(user),
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _advance(client: AsyncClient, user: User, deal_id: int, **body):
    return await client.post(f"/api/deals/{deal_id}/advance", json=body, headers=_auth(user))


def _active_names(deal: dict) -> list[str]:
    return sorted(stage["stage_name"] for stage in deal["active_stages"])


@pytest.mark.asyncio
async def test_create_deal_starts_at_first_stage(client, worker_user, processes):
    deal = await _create(client, worker_user)
    assert deal["status"] == "active"
    assert _active_names(deal) == ["Start"]
    assert len(deal["history"]) == 1


@pytest.mark.asyncio
async def test_create_deal_unknown_process(client, worker_user):
    response = await client.post(
        "/api/deals/",
        json={"process_type": "Nope", "client_name": "C", "client_phone": "1"},
        headers=_auth(worker_user),
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_deal_requires_seeded_catalog(client, worker_user, monkeypatch):
    monkeypatch.setitem(PROCESSES, FLOW.name, FLOW)
    response = await client.post(
        "/api/deals/",
        json={"process_type": "Flow", "client_name": "C", "client_phone": "1"},
        headers=_auth(worker_user),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_missing_deal(client, worker_user):
    response = await client.get("/api/deals/999", headers=_auth(worker_user))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_advance_linear_stage(client, worker_user, processes):
    deal = await _create(client, worker_user)
    response = await _advance(client, worker_user, deal["id"])
    assert response.status_code == 200
    body = response.json()
    assert _active_names(body) == ["Gate"]
    assert body["current_stage_is_decision"] is True
    assert body["history"][0]["status"] == "done"


@pytest.mark.asyncio
async def test_decision_stage_requires_decision(client, worker_user, processes):
    deal = await _create(client, worker_user)
    await _advance(client, worker_user, deal["id"])
    response = await _advance(client, worker_user, deal["id"])
    assert response.status_code == 409
    assert "рішення" in response.json()["detail"]


@pytest.mark.asyncio
async def test_no_branch_closes_deal_and_blocks_further_moves(client, worker_user, processes):
    deal = await _create(client, worker_user)
    await _advance(client, worker_user, deal["id"])
    closed = (await _advance(client, worker_user, deal["id"], decision=False)).json()
    assert closed["status"] == "closed"
    assert closed["active_stages"] == []

    response = await _advance(client, worker_user, deal["id"])
    assert response.status_code == 409


async def _to_fan_out(client: AsyncClient, user: User) -> dict:
    deal = await _create(client, user)
    await _advance(client, user, deal["id"])
    await _advance(client, user, deal["id"], decision=True)
    return (await _advance(client, user, deal["id"])).json()


@pytest.mark.asyncio
async def test_parallel_branches_need_progress_id(client, worker_user, processes):
    deal = await _to_fan_out(client, worker_user)
    assert _active_names(deal) == ["Left", "Right"]

    response = await _advance(client, worker_user, deal["id"])
    assert response.status_code == 409
    assert "progress_id" in response.json()["detail"]


@pytest.mark.asyncio
async def test_unknown_progress_id(client, worker_user, processes):
    deal = await _to_fan_out(client, worker_user)
    response = await _advance(client, worker_user, deal["id"], progress_id=999999)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_and_join_completes_only_after_last_branch(client, worker_user, processes):
    deal = await _to_fan_out(client, worker_user)
    left, right = sorted(deal["active_stages"], key=lambda stage: stage["stage_name"])

    after_first = (await _advance(client, worker_user, deal["id"], progress_id=left["id"])).json()
    assert after_first["status"] == "active"
    assert _active_names(after_first) == ["Right"]

    after_second = (await _advance(client, worker_user, deal["id"], progress_id=right["id"])).json()
    assert after_second["status"] == "completed"
    assert after_second["active_stages"] == []


@pytest.mark.asyncio
async def test_terminal_reached_alongside_new_branch_keeps_deal_active(client, worker_user, processes):
    deal = await _create(client, worker_user, "Mixed")
    body = (await _advance(client, worker_user, deal["id"])).json()
    assert body["status"] == "active"
    assert _active_names(body) == ["Open"]


@pytest.mark.asyncio
async def test_comment_is_saved_on_completed_stage(client, worker_user, processes):
    deal = await _create(client, worker_user)
    body = (await _advance(client, worker_user, deal["id"], comment="Done by phone")).json()
    assert body["history"][0]["comments"][0]["comment_text"] == "Done by phone"


@pytest.mark.asyncio
async def test_deal_endpoints_require_auth(client):
    response = await client.get("/api/deals/")
    assert response.status_code == 401
