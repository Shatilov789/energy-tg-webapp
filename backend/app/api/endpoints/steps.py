"""Step answer endpoints — workers fill in answers for scenario steps."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.security import get_current_user
from backend.app.db.session import get_db
from backend.app.models.answer import ObjectAnswer
from backend.app.models.audit import AuditAction
from backend.app.models.comment import StepComment
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.object import Object, ObjectWorker
from backend.app.models.user import User, UserRole
from backend.app.services.audit import log_action
from backend.app.schemas.answer import AnswerCreate, AnswerResponse
from backend.app.schemas.error import RESPONSES_CRUD, RESPONSES_CRUD_CONFLICT
from backend.app.schemas.step_comment import StepCommentCreate, StepCommentResponse

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
        comments=[],
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
        select(ObjectAnswer)
        .where(ObjectAnswer.object_id == object_id, ObjectAnswer.step_id == step_id)
        .options(selectinload(ObjectAnswer.comments))
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


@router.get("/{step_id}/comments", response_model=list[StepCommentResponse], responses=RESPONSES_CRUD)
async def list_step_comments(
    object_id: int,
    step_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List discussion thread for a step, oldest first."""
    await _verify_access(object_id, current_user, db)

    result = await db.execute(
        select(StepComment)
        .where(StepComment.object_id == object_id, StepComment.step_id == step_id)
        .options(selectinload(StepComment.author), selectinload(StepComment.recipient))
        .order_by(StepComment.created_at.asc())
    )
    return result.scalars().all()


@router.post("/{step_id}/comments", response_model=StepCommentResponse, status_code=status.HTTP_201_CREATED, responses=RESPONSES_CRUD)
async def add_step_comment(
    object_id: int,
    step_id: int,
    data: StepCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Post a message to the step's discussion thread, optionally mentioning a colleague."""
    await _verify_access(object_id, current_user, db)

    comment = StepComment(
        object_id=object_id,
        step_id=step_id,
        author_id=current_user.id,
        recipient_id=data.recipient_id,
        comment_text=data.comment_text,
    )
    db.add(comment)
    await db.flush()

    if data.recipient_id and data.recipient_id != current_user.id:
        notification = Notification(
            user_id=data.recipient_id,
            type=NotificationType.STEP_COMMENT,
            title="New mention in step discussion",
            message=f"{current_user.first_name} mentioned you in a comment",
        )
        db.add(notification)
        await db.flush()

    await log_action(
        db, user_id=current_user.id, action=AuditAction.COMMENT,
        entity_type="step_comment", entity_id=comment.id,
        details={"object_id": object_id, "step_id": step_id, "recipient_id": data.recipient_id},
    )

    result = await db.execute(
        select(StepComment)
        .where(StepComment.id == comment.id)
        .options(selectinload(StepComment.author), selectinload(StepComment.recipient))
    )
    return result.scalar_one()


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
