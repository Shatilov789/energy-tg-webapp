"""Scenario CRUD endpoints — admin creates/edits, workers read."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.security import get_current_user, require_admin
from backend.app.db.session import get_db
from backend.app.models.scenario import Scenario, ScenarioStep
from backend.app.models.user import User
from backend.app.schemas.error import RESPONSES_AUTH, RESPONSES_CRUD
from backend.app.schemas.scenario import (
    ScenarioCreate,
    ScenarioResponse,
    ScenarioStepCreate,
    ScenarioStepResponse,
    ScenarioWithStepsResponse,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("/", response_model=list[ScenarioResponse], responses=RESPONSES_AUTH)
async def list_scenarios(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active scenarios."""
    result = await db.execute(
        select(Scenario).where(Scenario.is_active.is_(True), Scenario.is_deleted.is_(False)).order_by(Scenario.id)
    )
    return result.scalars().all()


@router.get("/{scenario_id}", response_model=ScenarioWithStepsResponse, responses=RESPONSES_CRUD)
async def get_scenario(
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get scenario with all steps."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id).options(selectinload(Scenario.steps)))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сценарій не знайдено")
    return scenario


@router.post("/", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED, responses=RESPONSES_AUTH)
async def create_scenario(
    data: ScenarioCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create new scenario (admin only)."""
    scenario = Scenario(name=data.name, description=data.description)
    db.add(scenario)
    await db.flush()
    return scenario


@router.post(
    "/{scenario_id}/steps",
    response_model=ScenarioStepResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESPONSES_CRUD,
)
async def add_step(
    scenario_id: int,
    data: ScenarioStepCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add step to scenario (admin only)."""
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сценарій не знайдено")

    step = ScenarioStep(
        scenario_id=scenario_id,
        step_number=data.step_number,
        question_text=data.question_text,
        description=data.description,
        is_required=data.is_required,
    )
    db.add(step)
    await db.flush()
    return step
