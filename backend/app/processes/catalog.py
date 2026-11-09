"""Syncs each process's stage catalog to the database. Safe to run on every startup."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.deal import Stage
from backend.app.processes.definition import ProcessDefinition
from backend.app.processes.registry import PROCESSES

logger = logging.getLogger(__name__)


async def seed_process(db: AsyncSession, process: ProcessDefinition) -> None:
    """Bring the process's stages in the database in line with its definition.

    Stages match by stage_key. One removed from the definition stays in the database, because
    deals may still reference it, and is reported in the log.
    """
    result = await db.execute(select(Stage).where(Stage.parent_process == process.name))
    stored = {stage.stage_key: stage for stage in result.scalars()}
    added = updated = 0

    for order_index, (display_code, stage_key, name, role_owner, is_decision) in enumerate(process.stages, start=1):
        yes_label, no_label = process.decision_labels.get(stage_key, (None, None))
        values = {
            "display_code": display_code,
            "name": name,
            "role_owner": role_owner,
            "order_index": order_index,
            "is_decision": is_decision,
            "yes_label": yes_label,
            "no_label": no_label,
        }
        stage = stored.pop(stage_key, None)
        if stage is None:
            db.add(Stage(stage_key=stage_key, parent_process=process.name, **values))
            added += 1
        elif any(getattr(stage, field) != value for field, value in values.items()):
            for field, value in values.items():
                setattr(stage, field, value)
            updated += 1

    await db.commit()
    logger.info("%s catalog: %d added, %d updated", process.name, added, updated)
    if stored:
        logger.warning("%s: stages no longer defined, kept in the database: %s", process.name, sorted(stored))


async def seed_process_catalog(db: AsyncSession) -> None:
    """Seed every registered process."""
    for process in PROCESSES.values():
        await seed_process(db, process)
