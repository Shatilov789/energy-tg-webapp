"""Object CRUD endpoints — worker creates/manages inspection objects."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.security import get_current_user
from backend.app.db.session import get_db
from backend.app.models.audit import AuditAction
from backend.app.models.object import Object, ObjectStatus, ObjectWorker
from backend.app.models.scenario import Scenario
from backend.app.models.user import User
from backend.app.services.audit import log_action
from backend.app.schemas.error import RESPONSES_AUTH, RESPONSES_CRUD, RESPONSES_CRUD_CONFLICT
from backend.app.schemas.object import ObjectCreate, ObjectDetailResponse, ObjectListItemResponse, ObjectResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/objects", tags=["objects"])


@router.get("/", response_model=list[ObjectListItemResponse], responses=RESPONSES_AUTH)
async def list_my_objects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List objects where current user is creator or shared worker, with progress meta in one query."""
    result = await db.execute(
        select(Object)
        .outerjoin(ObjectWorker, ObjectWorker.object_id == Object.id)
        .where(
            (Object.created_by_id == current_user.id) | (ObjectWorker.user_id == current_user.id),
            Object.is_deleted.is_(False),
        )
        .options(
            selectinload(Object.scenario).selectinload(Scenario.steps),
            selectinload(Object.answers),
        )
        .distinct()
        .order_by(Object.updated_at.desc())
    )
    objects = result.scalars().all()

    items = []
    for obj in objects:
        steps = sorted(obj.scenario.steps, key=lambda s: s.step_number) if obj.scenario else []
        answered_ids = {a.step_id for a in obj.answers}
        next_step_obj = next((s for s in steps if s.id not in answered_ids), None)
        items.append(
            ObjectListItemResponse(
                **ObjectResponse.model_validate(obj).model_dump(),
                scenario_name=obj.scenario.name if obj.scenario else "",
                total_steps=len(steps),
                answered_steps=len(answered_ids),
                next_step=next_step_obj.step_number if next_step_obj else (steps[-1].step_number if steps else 1),
            )
        )
    return items


@router.get("/{object_id}", response_model=ObjectDetailResponse, responses=RESPONSES_CRUD)
async def get_object(
    object_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get object with answers and progress."""
    obj = await _get_object_with_access(object_id, current_user, db)
    return obj


@router.post("/", response_model=ObjectResponse, status_code=status.HTTP_201_CREATED, responses=RESPONSES_AUTH)
async def create_object(
    data: ObjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new inspection object."""
    obj = Object(
        name=data.name,
        comment=data.comment,
        scenario_id=data.scenario_id,
        created_by_id=current_user.id,
    )
    db.add(obj)
    await db.flush()

    worker_link = ObjectWorker(object_id=obj.id, user_id=current_user.id)
    db.add(worker_link)
    await db.flush()

    await log_action(
        db, user_id=current_user.id, action=AuditAction.CREATE,
        entity_type="object", entity_id=obj.id,
        details={"name": data.name, "scenario_id": data.scenario_id},
    )
    return obj


@router.post("/{object_id}/share/{user_id}", status_code=status.HTTP_201_CREATED, responses=RESPONSES_CRUD_CONFLICT)
async def share_object(
    object_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Share object with another worker."""
    obj = await _get_object_with_access(object_id, current_user, db)

    existing = await db.execute(
        select(ObjectWorker).where(ObjectWorker.object_id == object_id, ObjectWorker.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already has access")

    db.add(ObjectWorker(object_id=object_id, user_id=user_id))
    await db.flush()
    await log_action(
        db, user_id=current_user.id, action=AuditAction.SHARE,
        entity_type="object", entity_id=object_id,
        details={"shared_with_user_id": user_id},
    )
    return {"detail": "Object shared"}


async def _get_object_with_access(object_id: int, user: User, db: AsyncSession) -> Object:
    """Fetch object and verify user has access."""
    result = await db.execute(
        select(Object)
        .where(Object.id == object_id)
        .options(
            selectinload(Object.scenario).selectinload(Scenario.steps),
            selectinload(Object.answers),
            selectinload(Object.workers),
        )
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")

    has_access = obj.created_by_id == user.id or any(w.user_id == user.id for w in obj.workers)
    from backend.app.models.user import UserRole
    if user.role == UserRole.ADMIN:
        has_access = True

    if not has_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this object")
    return obj
