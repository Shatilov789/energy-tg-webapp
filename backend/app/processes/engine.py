"""Workflow engine: starts deals and moves them along their process graph.

Knows nothing about HTTP. Failures are raised as WorkflowError subclasses and translated to
responses by the API layer.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.audit import AuditAction
from backend.app.models.deal import Deal, DealStageComment, DealStageProgress, DealStatus, Stage, StageStatus
from backend.app.models.user import User
from backend.app.processes.definition import DecisionRequired, ProcessDefinition
from backend.app.processes.registry import PROCESSES
from backend.app.services.audit import log_action


class WorkflowError(Exception):
    """A deal operation that cannot be carried out."""


class UnknownProcess(WorkflowError):
    pass


class CatalogNotSeeded(WorkflowError):
    pass


class DealNotFound(WorkflowError):
    pass


class DealNotActive(WorkflowError):
    pass


class NoStageInProgress(WorkflowError):
    pass


class ProgressNotFound(WorkflowError):
    pass


class StageAlreadyCompleted(WorkflowError):
    """The requested stage belongs to the deal but was already completed, e.g. from a stale tab."""


class AmbiguousProgress(WorkflowError):
    """Several branches are in progress and the caller did not say which one to complete."""

    def __init__(self, progress_ids: list[int]):
        super().__init__(progress_ids)
        self.progress_ids = progress_ids


class StageDecisionRequired(WorkflowError):
    pass


class StageNoLongerDefined(WorkflowError):
    """The deal sits on a stage that was removed from its process definition."""


def get_process(process_type: str) -> ProcessDefinition:
    process = PROCESSES.get(process_type)
    if not process:
        raise UnknownProcess(process_type)
    return process


async def load_deal(db: AsyncSession, deal_id: int, *, for_update: bool = False) -> Deal:
    """Fetch a deal with its stages and comments, optionally locking its row."""
    query = (
        select(Deal)
        .where(Deal.id == deal_id)
        .options(
            selectinload(Deal.current_stage),
            selectinload(Deal.progress).selectinload(DealStageProgress.stage),
            selectinload(Deal.progress).selectinload(DealStageProgress.comments),
        )
        .execution_options(populate_existing=True)
    )
    if for_update:
        query = query.with_for_update()

    deal = (await db.execute(query)).scalar_one_or_none()
    if not deal:
        raise DealNotFound(deal_id)
    return deal


async def start_deal(
    db: AsyncSession,
    *,
    actor: User,
    process_type: str,
    client_name: str,
    client_phone: str,
    client_email: str | None = None,
    object_address: str | None = None,
    lead_source: str | None = None,
) -> Deal:
    """Register a new deal, in progress at the first stage of its process."""
    process = get_process(process_type)
    first_stage_key = process.stages[0][1]
    first_stage = (
        await db.execute(select(Stage).where(Stage.parent_process == process.name, Stage.stage_key == first_stage_key))
    ).scalar_one_or_none()
    if not first_stage:
        raise CatalogNotSeeded(process.name)

    deal = Deal(
        process_type=process.name,
        client_name=client_name,
        client_phone=client_phone,
        client_email=client_email,
        object_address=object_address,
        lead_source=lead_source,
        created_by_id=actor.id,
        current_stage_id=first_stage.id,
    )
    db.add(deal)
    await db.flush()

    db.add(
        DealStageProgress(
            deal_id=deal.id,
            stage_id=first_stage.id,
            status=StageStatus.IN_PROGRESS,
            assigned_user_id=actor.id,
            started_at=datetime.now(UTC),
        )
    )
    await db.flush()

    await log_action(
        db,
        user_id=actor.id,
        action=AuditAction.CREATE,
        entity_type="deal",
        entity_id=deal.id,
        deal_id=deal.id,
        details={"client_name": client_name},
    )
    return await load_deal(db, deal.id)


async def advance_deal(
    db: AsyncSession,
    *,
    deal_id: int,
    actor: User,
    decision: bool | None = None,
    comment: str | None = None,
    progress_id: int | None = None,
) -> Deal:
    """Complete one in-progress stage and enter whatever follows it in the process graph.

    The deal row stays locked until commit, so a double tap cannot complete a stage twice.
    """
    deal = await load_deal(db, deal_id, for_update=True)
    if deal.status != DealStatus.ACTIVE:
        raise DealNotActive(deal_id)

    current = _select_progress(deal, progress_id)
    if current.stage.is_decision and decision is None:
        raise StageDecisionRequired(current.stage.stage_key)

    process = get_process(deal.process_type)
    if current.stage.stage_key not in process.transitions:
        raise StageNoLongerDefined(current.stage.stage_key)

    try:
        next_keys = process.resolve_next(current.stage.stage_key, decision)
    except DecisionRequired as exc:
        raise StageDecisionRequired(current.stage.stage_key) from exc

    now = datetime.now(UTC)
    current.status = StageStatus.DONE
    current.decision = decision
    current.completed_at = now

    if comment:
        db.add(DealStageComment(deal_stage_progress_id=current.id, author_id=actor.id, comment_text=comment))

    for stage_key in next_keys:
        await _enter_stage(db, deal, process, stage_key, actor, now)
    await db.flush()

    # AND-join: a "completed" terminal finishes the deal only once no branch is still open.
    reached_completion = any(process.terminal_status(key) == "completed" for key in next_keys)
    if reached_completion and not any(p.status == StageStatus.IN_PROGRESS for p in deal.progress):
        deal.status = DealStatus.COMPLETED
        await db.flush()

    await log_action(
        db,
        user_id=actor.id,
        action=AuditAction.UPDATE,
        entity_type="deal_stage_progress",
        entity_id=current.id,
        deal_id=deal.id,
        details={"stage": current.stage.stage_key, "decision": decision},
    )
    return await load_deal(db, deal.id)


def _select_progress(deal: Deal, progress_id: int | None) -> DealStageProgress:
    """Pick the in-progress row to complete: the requested one, or the only one there is."""
    if progress_id is not None:
        selected = next((p for p in deal.progress if p.id == progress_id), None)
        if not selected:
            raise ProgressNotFound(progress_id)
        if selected.status == StageStatus.DONE:
            raise StageAlreadyCompleted(progress_id)
        if selected.status != StageStatus.IN_PROGRESS:
            raise ProgressNotFound(progress_id)
        return selected

    in_progress = [p for p in deal.progress if p.status == StageStatus.IN_PROGRESS]
    if not in_progress:
        raise NoStageInProgress(deal.id)

    if len(in_progress) > 1:
        raise AmbiguousProgress([p.id for p in in_progress])
    return in_progress[0]


async def _enter_stage(
    db: AsyncSession,
    deal: Deal,
    process: ProcessDefinition,
    stage_key: str,
    actor: User,
    now: datetime,
) -> None:
    """Append the progress row for a stage the deal has just reached."""
    stage = (
        await db.execute(select(Stage).where(Stage.parent_process == process.name, Stage.stage_key == stage_key))
    ).scalar_one()

    terminal = process.terminal_status(stage_key)
    # Appending through the relationship keeps deal.progress current for the AND-join check.
    if terminal:
        deal.progress.append(
            DealStageProgress(stage_id=stage.id, status=StageStatus.DONE, started_at=now, completed_at=now)
        )
        if terminal == "closed":
            deal.status = DealStatus.CLOSED
    else:
        deal.progress.append(
            DealStageProgress(
                stage_id=stage.id,
                status=StageStatus.IN_PROGRESS,
                assigned_user_id=actor.id,
                started_at=now,
            )
        )
    deal.current_stage_id = stage.id
