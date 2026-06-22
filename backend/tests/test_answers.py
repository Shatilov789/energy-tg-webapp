"""
Тесты заполнения шагов (/api/objects/{id}/steps/{step_id}/answer).

ПРОВЕРЯЕМ:
- Работник отвечает на шаг → 201, ответ сохранен, is_locked=True
- Повторный ответ на тот же шаг → 409 Conflict
- Редактирование заблокированного ответа → 403
- Админ разблокирует → работник может редактировать
- Расшаренный работник может отвечать на шаги
- Работник без доступа не может отвечать → 403

БИЗНЕС-ЛОГИКА:
- Каждый шаг можно заполнить только один раз (POST создает, PUT обновляет)
- Сразу после создания ответ блокируется (is_locked=True)
- Редактировать можно только после разблокировки админом
- Видно кто заполнил каждый шаг (answered_by_id)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.scenario import Scenario, ScenarioStep
from backend.app.models.user import User


async def _setup_object(client: AsyncClient, db: AsyncSession, worker: User) -> tuple[int, int]:
    """
    Хелпер: создает сценарий (1 шаг) + объект.
    Возвращает (object_id, step_id) для тестов.
    """
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
        headers={"X-Dev-Telegram-Id": str(worker.telegram_id)},
    )
    return res.json()["id"], step.id


@pytest.mark.asyncio
async def test_submit_answer(client: AsyncClient, worker_user: User, db: AsyncSession):
    """
    Работник заполняет шаг → 201.
    Ответ сохраняется с текстом, привязан к работнику, сразу заблокирован.
    """
    obj_id, step_id = await _setup_object(client, db, worker_user)

    response = await client.post(
        f"/api/objects/{obj_id}/steps/{step_id}/answer",
        json={"answer_text": "Everything is fine"},
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["answer_text"] == "Everything is fine"
    assert data["is_locked"] is True  # сразу заблокирован
    assert data["answered_by_id"] == worker_user.id


@pytest.mark.asyncio
async def test_duplicate_answer_rejected(client: AsyncClient, worker_user: User, db: AsyncSession):
    """
    Повторный POST на тот же шаг → 409 Conflict.
    Нельзя создать два ответа на один шаг. Для редактирования используй PUT.
    """
    obj_id, step_id = await _setup_object(client, db, worker_user)
    headers = {"X-Dev-Telegram-Id": str(worker_user.telegram_id)}

    # Первый ответ — ok
    await client.post(
        f"/api/objects/{obj_id}/steps/{step_id}/answer",
        json={"answer_text": "First answer"},
        headers=headers,
    )

    # Второй ответ на тот же шаг — конфликт
    response = await client.post(
        f"/api/objects/{obj_id}/steps/{step_id}/answer",
        json={"answer_text": "Second answer"},
        headers=headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_locked_answer_forbidden(client: AsyncClient, worker_user: User, db: AsyncSession):
    """
    PUT на заблокированный ответ → 403.
    Работник не может редактировать без разрешения админа.
    """
    obj_id, step_id = await _setup_object(client, db, worker_user)
    headers = {"X-Dev-Telegram-Id": str(worker_user.telegram_id)}

    await client.post(
        f"/api/objects/{obj_id}/steps/{step_id}/answer",
        json={"answer_text": "Locked answer"},
        headers=headers,
    )

    response = await client.put(
        f"/api/objects/{obj_id}/steps/{step_id}/answer",
        json={"answer_text": "Edited"},
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_unlock_then_worker_edits(
    client: AsyncClient, admin_user: User, worker_user: User, db: AsyncSession
):
    """
    Полный цикл: работник отвечает → админ разблокирует → работник редактирует.
    1. Worker POST answer → is_locked=True
    2. Admin PATCH /unlock → is_locked=False
    3. Worker PUT answer → 200, текст обновлен
    """
    obj_id, step_id = await _setup_object(client, db, worker_user)
    worker_h = {"X-Dev-Telegram-Id": str(worker_user.telegram_id)}
    admin_h = {"X-Dev-Telegram-Id": str(admin_user.telegram_id)}

    # 1. Работник отвечает
    res = await client.post(
        f"/api/objects/{obj_id}/steps/{step_id}/answer",
        json={"answer_text": "Original"},
        headers=worker_h,
    )
    answer_id = res.json()["id"]

    # 2. Админ разблокирует
    unlock_res = await client.patch(f"/api/admin/answers/{answer_id}/unlock", headers=admin_h)
    assert unlock_res.status_code == 200

    # 3. Работник редактирует
    edit_res = await client.put(
        f"/api/objects/{obj_id}/steps/{step_id}/answer",
        json={"answer_text": "Updated"},
        headers=worker_h,
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["answer_text"] == "Updated"


@pytest.mark.asyncio
async def test_shared_worker_can_answer(
    client: AsyncClient, worker_user: User, second_worker: User, db: AsyncSession
):
    """
    Расшаренный работник может заполнять шаги.
    1. Worker 1 создает объект
    2. Worker 1 расшаривает Worker 2
    3. Worker 2 отвечает на шаг → 201, answered_by = Worker 2
    """
    obj_id, step_id = await _setup_object(client, db, worker_user)

    # Расшариваем
    await client.post(
        f"/api/objects/{obj_id}/share/{second_worker.id}",
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )

    # Второй работник отвечает
    response = await client.post(
        f"/api/objects/{obj_id}/steps/{step_id}/answer",
        json={"answer_text": "Answer from worker 2"},
        headers={"X-Dev-Telegram-Id": str(second_worker.telegram_id)},
    )
    assert response.status_code == 201
    assert response.json()["answered_by_id"] == second_worker.id


@pytest.mark.asyncio
async def test_no_access_worker_cannot_answer(
    client: AsyncClient, worker_user: User, second_worker: User, db: AsyncSession
):
    """Работник без доступа к объекту не может отвечать на шаги → 403."""
    obj_id, step_id = await _setup_object(client, db, worker_user)

    response = await client.post(
        f"/api/objects/{obj_id}/steps/{step_id}/answer",
        json={"answer_text": "Should fail"},
        headers={"X-Dev-Telegram-Id": str(second_worker.telegram_id)},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_nonexistent_answer(client: AsyncClient, worker_user: User, db: AsyncSession):
    """PUT на шаг без ответа → 404."""
    obj_id, step_id = await _setup_object(client, db, worker_user)

    response = await client.put(
        f"/api/objects/{obj_id}/steps/{step_id}/answer",
        json={"answer_text": "No answer yet"},
        headers={"X-Dev-Telegram-Id": str(worker_user.telegram_id)},
    )
    assert response.status_code == 404
