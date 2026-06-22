"""
Тесты CRUD сценариев (/api/scenarios/).

ПРОВЕРЯЕМ:
- Админ создает сценарий → 201
- Работник НЕ может создать сценарий → 403
- Любой авторизованный пользователь видит список сценариев
- Админ добавляет шаги к сценарию
- Получение сценария со всеми шагами
- Несуществующий сценарий → 404

КАК УСТРОЕНЫ СЦЕНАРИИ:
- Сценарий = шаблон проверки (например "Подстанция")
- Внутри сценария — шаги (до 40), каждый шаг = один вопрос
- Создавать/редактировать может только админ
- Работники только читают и заполняют
"""

import pytest
from httpx import AsyncClient

from backend.app.models.user import User


@pytest.mark.asyncio
async def test_create_scenario_as_admin(client: AsyncClient, admin_user: User):
    """Админ создает сценарий → 201, возвращает id, name, is_active=True."""
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
    """Работник пытается создать сценарий → 403 Forbidden. Только админ может."""
    response = await client.post(
        "/api/scenarios/",
        json={"name": "Should Fail"},
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_scenarios(client: AsyncClient, admin_user: User, worker_user: User):
    """
    Работник видит сценарии созданные админом.
    1. Админ создает сценарий
    2. Работник делает GET /scenarios/ → видит его в списке
    """
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
    """
    Админ добавляет шаг (вопрос) к сценарию.
    step_number — порядковый номер, question_text — текст вопроса.
    """
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
    """
    GET /scenarios/{id} возвращает сценарий вместе со всеми шагами.
    Шаги отсортированы по step_number.
    """
    headers = {"X-Dev-Telegram-Id": str(admin_user.telegram_id)}

    res = await client.post("/api/scenarios/", json={"name": "Full Scenario"}, headers=headers)
    sid = res.json()["id"]

    # Добавляем 3 шага
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
    """Запрос несуществующего сценария → 404."""
    response = await client.get(
        "/api/scenarios/99999",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_step_to_nonexistent_scenario(client: AsyncClient, admin_user: User):
    """Добавление шага к несуществующему сценарию → 404."""
    response = await client.post(
        "/api/scenarios/99999/steps",
        json={"step_number": 1, "question_text": "Q?"},
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 404
