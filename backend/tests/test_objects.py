"""
Тесты CRUD объектов (/api/objects/).

ПРОВЕРЯЕМ:
- Работник создает объект → 201, статус in_progress
- Работник видит только свои объекты (+ расшаренные)
- Детальный просмотр объекта с ответами
- Расшаривание объекта другому работнику
- Повторное расшаривание → 409 Conflict
- Чужой работник без доступа → 403
- Админ видит любой объект (имеет полный доступ)
- Несуществующий объект → 404

КАК УСТРОЕНЫ ОБЪЕКТЫ:
- Объект = конкретная проверка (например "ПС-12 · Подстанция")
- Привязан к сценарию (определяет список шагов)
- Создатель автоматически добавляется в object_workers
- Можно расшарить другим работникам — оба заполняют, видно кто что
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.scenario import Scenario, ScenarioStep
from backend.app.models.user import User


async def _create_scenario_with_steps(db: AsyncSession, num_steps: int = 3) -> Scenario:
    """
    Хелпер: создает сценарий с N шагами напрямую в БД.
    Используется вместо API — быстрее и не зависит от тестов сценариев.
    """
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
    """
    Работник создает объект проверки.
    Передает: name, comment (опционально), scenario_id.
    Получает: объект со статусом in_progress.
    """
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
    """
    GET /objects/ — возвращает только объекты текущего пользователя.
    Создаем 2 объекта → видим 2 в списке.
    """
    scenario = await _create_scenario_with_steps(db)
    headers = {"X-Dev-Telegram-Id": str(worker_user.telegram_id)}

    await client.post("/api/objects/", json={"name": "Obj A", "scenario_id": scenario.id}, headers=headers)
    await client.post("/api/objects/", json={"name": "Obj B", "scenario_id": scenario.id}, headers=headers)

    response = await client.get("/api/objects/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_object_detail(client: AsyncClient, worker_user: User, db: AsyncSession):
    """
    GET /objects/{id} — детальный просмотр объекта.
    Возвращает объект с вложенными: scenario, answers.
    """
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
    """Запрос несуществующего объекта → 404."""
    response = await client.get(
        "/api/objects/99999",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_share_object(client: AsyncClient, worker_user: User, second_worker: User, db: AsyncSession):
    """
    Расшаривание объекта другому работнику.
    1. Worker 1 создает объект
    2. Worker 1 расшаривает Worker 2 → 201
    3. Повторное расшаривание → 409 Conflict (уже есть доступ)
    """
    scenario = await _create_scenario_with_steps(db)

    res = await client.post(
        "/api/objects/",
        json={"name": "Shared Obj", "scenario_id": scenario.id},
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    obj_id = res.json()["id"]

    # Расшариваем
    response = await client.post(
        f"/api/objects/{obj_id}/share/{second_worker.id}",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 201

    # Повторная попытка → конфликт
    response = await client.post(
        f"/api/objects/{obj_id}/share/{second_worker.id}",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_shared_worker_sees_object(client: AsyncClient, worker_user: User, second_worker: User, db: AsyncSession):
    """
    После расшаривания второй работник видит объект в своем списке
    и может открыть его детали.
    """
    scenario = await _create_scenario_with_steps(db)
    w1_h = {"X-Dev-Telegram-Id": str(worker_user.telegram_id)}
    w2_h = {"X-Dev-Telegram-Id": str(second_worker.telegram_id)}

    res = await client.post(
        "/api/objects/",
        json={"name": "Shared View", "scenario_id": scenario.id},
        headers=w1_h,
    )
    obj_id = res.json()["id"]

    # До расшаривания — worker 2 не видит
    list_res = await client.get("/api/objects/", headers=w2_h)
    assert len(list_res.json()) == 0

    # Расшариваем
    await client.post(f"/api/objects/{obj_id}/share/{second_worker.id}", headers=w1_h)

    # После расшаривания — worker 2 видит
    list_res = await client.get("/api/objects/", headers=w2_h)
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["name"] == "Shared View"


@pytest.mark.asyncio
async def test_object_access_forbidden_for_other_worker(
    client: AsyncClient, worker_user: User, second_worker: User, db: AsyncSession
):
    """
    Работник БЕЗ доступа не может открыть чужой объект → 403.
    Проверяет изоляцию данных между работниками.
    """
    scenario = await _create_scenario_with_steps(db)

    res = await client.post(
        "/api/objects/",
        json={"name": "Private Obj", "scenario_id": scenario.id},
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    obj_id = res.json()["id"]

    # Второй работник пытается открыть → запрещено
    response = await client.get(
        f"/api/objects/{obj_id}",
        headers={"X-Dev-Telegram-Id": str(second_worker.telegram_id)},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_see_any_object(
    client: AsyncClient, admin_user: User, worker_user: User, db: AsyncSession
):
    """
    Админ имеет доступ к любому объекту любого работника.
    Это нужно для контроля и комментирования.
    """
    scenario = await _create_scenario_with_steps(db)

    res = await client.post(
        "/api/objects/",
        json={"name": "Worker Obj", "scenario_id": scenario.id},
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    obj_id = res.json()["id"]

    # Админ открывает объект работника → 200
    response = await client.get(
        f"/api/objects/{obj_id}",
        headers={"X-Dev-Telegram-Id": str(admin_user.telegram_id)},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Worker Obj"
