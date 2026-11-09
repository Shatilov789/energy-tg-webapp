"""Deal endpoints: HTTP layer over the workflow engine in backend.app.processes.engine."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.security import get_current_user
from backend.app.db.session import get_db
from backend.app.models.deal import Deal, DealStageProgress, Stage, StageStatus
from backend.app.models.user import User
from backend.app.processes import engine
from backend.app.schemas.deal import (
    DealAdvance,
    DealCreate,
    DealDetailResponse,
    DealListItemResponse,
    DealStageProgressResponse,
    StageResponse,
)
from backend.app.schemas.error import RESPONSES_AUTH, RESPONSES_CRUD

router = APIRouter(prefix="/deals", tags=["deals"])


def _to_http_error(exc: engine.WorkflowError) -> HTTPException:
    match exc:
        case engine.UnknownProcess():
            return HTTPException(status.HTTP_400_BAD_REQUEST, f"Невідомий процес: {exc}")
        case engine.CatalogNotSeeded():
            return HTTPException(status.HTTP_409_CONFLICT, "Довідник етапів не заповнено")
        case engine.DealNotFound():
            return HTTPException(status.HTTP_404_NOT_FOUND, "Угоду не знайдено")
        case engine.DealNotActive():
            return HTTPException(status.HTTP_409_CONFLICT, "Угода неактивна")
        case engine.NoStageInProgress():
            return HTTPException(status.HTTP_409_CONFLICT, "Немає етапу в роботі")
        case engine.ProgressNotFound():
            return HTTPException(status.HTTP_404_NOT_FOUND, "Етап не знайдено або він неактивний")
        case engine.AmbiguousProgress():
            return HTTPException(
                status.HTTP_409_CONFLICT, f"Кілька етапів у роботі, вкажіть progress_id: {exc.progress_ids}"
            )
        case engine.StageDecisionRequired():
            return HTTPException(status.HTTP_409_CONFLICT, "Цей етап потребує рішення")
    raise exc


@router.get("/stages", response_model=list[StageResponse], responses=RESPONSES_AUTH)
async def list_stages(
    process_type: str = Query(default="СЕС"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the Stage catalog for a process, in process order."""
    result = await db.execute(select(Stage).where(Stage.parent_process == process_type).order_by(Stage.order_index))
    return result.scalars().all()


@router.get("/", response_model=list[DealListItemResponse], responses=RESPONSES_AUTH)
async def list_deals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all deals, newest first."""
    result = await db.execute(select(Deal).options(selectinload(Deal.current_stage)).order_by(Deal.created_at.desc()))
    return [_to_list_item(deal) for deal in result.scalars().all()]


@router.get("/{deal_id}", response_model=DealDetailResponse, responses=RESPONSES_CRUD)
async def get_deal(
    deal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get one deal with its current stage and full progress history."""
    try:
        return _to_detail(await engine.load_deal(db, deal_id))
    except engine.WorkflowError as exc:
        raise _to_http_error(exc) from exc


@router.post("/", response_model=DealDetailResponse, status_code=status.HTTP_201_CREATED, responses=RESPONSES_AUTH)
async def create_deal(
    data: DealCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a new deal at the first stage of its process."""
    try:
        deal = await engine.start_deal(
            db,
            actor=current_user,
            process_type=data.process_type,
            client_name=data.client_name,
            client_phone=data.client_phone,
            client_email=data.client_email,
            object_address=data.object_address,
            lead_source=data.lead_source,
        )
    except engine.WorkflowError as exc:
        raise _to_http_error(exc) from exc
    return _to_detail(deal)


@router.post("/{deal_id}/advance", response_model=DealDetailResponse, responses=RESPONSES_CRUD)
async def advance_deal(
    deal_id: int,
    data: DealAdvance,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Complete one in-progress stage and move the deal along its process graph."""
    try:
        deal = await engine.advance_deal(
            db,
            deal_id=deal_id,
            actor=current_user,
            decision=data.decision,
            comment=data.comment,
            progress_id=data.progress_id,
        )
    except engine.WorkflowError as exc:
        raise _to_http_error(exc) from exc
    return _to_detail(deal)


def _to_progress_response(progress: DealStageProgress) -> DealStageProgressResponse:
    return DealStageProgressResponse(
        id=progress.id,
        stage_id=progress.stage_id,
        stage_name=progress.stage.name,
        stage_code=progress.stage.display_code,
        is_decision=progress.stage.is_decision,
        yes_label=progress.stage.yes_label,
        no_label=progress.stage.no_label,
        status=progress.status.value,
        decision=progress.decision,
        started_at=progress.started_at,
        completed_at=progress.completed_at,
        comments=list(progress.comments),
    )


def _to_detail(deal: Deal) -> DealDetailResponse:
    history = [_to_progress_response(p) for p in sorted(deal.progress, key=lambda p: p.created_at)]
    active = [_to_progress_response(p) for p in deal.progress if p.status == StageStatus.IN_PROGRESS]
    return DealDetailResponse(
        **_to_list_item(deal).model_dump(),
        current_stage_is_decision=active[0].is_decision if len(active) == 1 else False,
        active_stages=active,
        history=history,
    )


def _to_list_item(deal: Deal) -> DealListItemResponse:
    return DealListItemResponse(
        id=deal.id,
        process_type=deal.process_type,
        client_name=deal.client_name,
        client_phone=deal.client_phone,
        client_email=deal.client_email,
        object_address=deal.object_address,
        lead_source=deal.lead_source,
        status=deal.status,
        closure_reason=deal.closure_reason,
        created_at=deal.created_at,
        current_stage_name=deal.current_stage.name if deal.current_stage else None,
        current_stage_code=deal.current_stage.display_code if deal.current_stage else None,
    )
