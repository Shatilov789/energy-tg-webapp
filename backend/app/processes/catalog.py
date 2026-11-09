"""Writes each process's stage catalog to the database. Safe to run on every startup."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.deal import Stage
from backend.app.processes.definition import ProcessDefinition
from backend.app.processes.registry import PROCESSES

logger = logging.getLogger(__name__)


async def seed_process(db: AsyncSession, process: ProcessDefinition) -> None:
    """Insert the process's stages, unless it already has a catalog."""
    existing = await db.execute(select(Stage).where(Stage.parent_process == process.name).limit(1))
    if existing.scalar_one_or_none():
        logger.info("%s stages already seeded, skipping", process.name)
        return

    for order_index, (display_code, stage_key, name, role_owner, is_decision) in enumerate(process.stages, start=1):
        yes_label, no_label = process.decision_labels.get(stage_key, (None, None))
        db.add(
            Stage(
                stage_key=stage_key,
                display_code=display_code,
                name=name,
                role_owner=role_owner,
                order_index=order_index,
                is_decision=is_decision,
                yes_label=yes_label,
                no_label=no_label,
                parent_process=process.name,
            )
        )

    await db.commit()
    logger.info("Seeded %d %s stages", len(process.stages), process.name)


async def seed_process_catalog(db: AsyncSession) -> None:
    """Seed every registered process."""
    for process in PROCESSES.values():
        await seed_process(db, process)
