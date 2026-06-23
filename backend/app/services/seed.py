"""Seed database with stub scenarios for development."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.scenario import Scenario, ScenarioStep
from backend.app.models.user import User, UserRole

logger = logging.getLogger(__name__)

STUB_SCENARIOS = [
    {
        "name": "Подстанция",
        "description": "Проверка состояния подстанции",
        "steps": [
            "Укажите тип подстанции",
            "Опишите общее состояние объекта",
            "Состояние силового трансформатора",
            "Состояние распределительного устройства",
            "Состояние заземляющего контура",
            "Состояние кабельных вводов",
            "Наличие и состояние средств защиты",
            "Состояние ограждения территории",
            "Состояние освещения",
            "Дополнительные замечания",
        ],
    },
    {
        "name": "КЛ линия",
        "description": "Проверка кабельной линии",
        "steps": [
            "Тип кабельной линии",
            "Протяженность участка (м)",
            "Состояние кабельной трассы",
            "Состояние муфт и соединений",
            "Наличие повреждений изоляции",
            "Состояние маркировки",
            "Состояние кабельных колодцев",
            "Результаты измерений сопротивления",
            "Состояние защитных покрытий",
            "Дополнительные замечания",
        ],
    },
    {
        "name": "Трансформатор",
        "description": "Проверка трансформатора",
        "steps": [
            "Тип трансформатора",
            "Номинальная мощность",
            "Состояние бака трансформатора",
            "Уровень масла",
            "Состояние вводов",
            "Состояние системы охлаждения",
            "Результаты замеров температуры",
            "Состояние заземления",
            "Наличие утечек масла",
            "Дополнительные замечания",
        ],
    },
    {
        "name": "Ремонт",
        "description": "Ремонтные работы на объекте",
        "steps": [
            "Тип ремонтных работ",
            "Описание неисправности",
            "Перечень необходимых материалов",
            "Выполненные работы — этап 1",
            "Выполненные работы — этап 2",
            "Выполненные работы — этап 3",
            "Результаты проверки после ремонта",
            "Замечания по качеству",
            "Рекомендации по дальнейшему обслуживанию",
            "Итоговое заключение",
        ],
    },
    {
        "name": "Проверка оборудования",
        "description": "Плановая проверка электрооборудования",
        "steps": [
            "Наименование оборудования",
            "Инвентарный номер",
            "Дата последней проверки",
            "Визуальный осмотр — результат",
            "Проверка механических частей",
            "Проверка электрических параметров",
            "Проверка средств защиты",
            "Соответствие нормативам",
            "Выявленные дефекты",
            "Заключение и рекомендации",
        ],
    },
]


async def seed_scenarios(db: AsyncSession) -> None:
    """Insert stub scenarios if database is empty."""
    result = await db.execute(select(Scenario).limit(1))
    if result.scalar_one_or_none():
        logger.info("Scenarios already seeded, skipping")
        return

    for scenario_data in STUB_SCENARIOS:
        scenario = Scenario(name=scenario_data["name"], description=scenario_data["description"])
        db.add(scenario)
        await db.flush()

        for i, question in enumerate(scenario_data["steps"], start=1):
            step = ScenarioStep(
                scenario_id=scenario.id,
                step_number=i,
                question_text=question,
            )
            db.add(step)

    await db.commit()
    logger.info("Seeded %d stub scenarios", len(STUB_SCENARIOS))


async def seed_dev_admin(db: AsyncSession) -> None:
    """Create a dev admin user if none exists."""
    result = await db.execute(select(User).where(User.role == UserRole.ADMIN).limit(1))
    if result.scalar_one_or_none():
        return

    admin_telegram_id = settings.admin_telegram_id or 123456789
    admin = User(
        telegram_id=admin_telegram_id,
        first_name="Dev",
        last_name="Admin",
        username="dev_admin",
        role=UserRole.ADMIN,
    )
    db.add(admin)

    worker = User(
        telegram_id=987654321,
        first_name="Dev",
        last_name="Worker",
        username="dev_worker",
        role=UserRole.WORKER,
    )
    db.add(worker)

    await db.commit()
    logger.info("Seeded dev admin (tg_id=123456789) and worker (tg_id=987654321)")
