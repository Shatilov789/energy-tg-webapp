"""Step answer endpoints — workers fill in answers for scenario steps."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import get_current_user
from backend.app.db.session import get_db
from backend.app.models.answer import ObjectAnswer
from backend.app.models.audit import AuditAction
from backend.app.models.object import Object, ObjectWorker
from backend.app.models.user import User, UserRole
from backend.app.services.audit import log_action
from backend.app.schemas.answer import AnswerCreate, AnswerResponse
from backend.app.schemas.error import RESPONSES_CRUD, RESPONSES_CRUD_CONFLICT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/objects/{object_id}/steps", tags=["steps"])


@router.post("/{step_id}/answer", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED, responses=RESPONSES_CRUD_CONFLICT)
async def submit_answer(
    object_id: int,
    step_id: int,
    data: AnswerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit answer for a specific step in an object."""
    await _verify_access(object_id, current_user, db)

    existing = await db.execute(
        select(ObjectAnswer).where(ObjectAnswer.object_id == object_id, ObjectAnswer.step_id == step_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Step already answered")

    answer = ObjectAnswer(
        object_id=object_id,
        step_id=step_id,
        answer_text=data.answer_text,
        answered_by_id=current_user.id,
    )
    db.add(answer)
    await db.flush()

    await log_action(
        db, user_id=current_user.id, action=AuditAction.CREATE,
        entity_type="answer", entity_id=answer.id,
        details={"object_id": object_id, "step_id": step_id},
    )
    return answer


@router.put("/{step_id}/answer", response_model=AnswerResponse, responses=RESPONSES_CRUD)
async def update_answer(
    object_id: int,
    step_id: int,
    data: AnswerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update answer — only if unlocked by admin."""
    result = await db.execute(
        select(ObjectAnswer).where(ObjectAnswer.object_id == object_id, ObjectAnswer.step_id == step_id)
    )
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")

    if answer.is_locked and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Answer locked — request admin unlock")

    answer.answer_text = data.answer_text
    answer.answered_by_id = current_user.id
    await db.flush()

    await log_action(
        db, user_id=current_user.id, action=AuditAction.UPDATE,
        entity_type="answer", entity_id=answer.id,
        details={"object_id": object_id, "step_id": step_id, "old_locked": False},
    )
    return answer


async def _verify_access(object_id: int, user: User, db: AsyncSession) -> None:
    """Check user has access to object."""
    result = await db.execute(select(Object).where(Object.id == object_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")

    if user.role == UserRole.ADMIN:
        return

    worker = await db.execute(
        select(ObjectWorker).where(ObjectWorker.object_id == object_id, ObjectWorker.user_id == user.id)
    )
    if not worker.scalar_one_or_none() and obj.created_by_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")
