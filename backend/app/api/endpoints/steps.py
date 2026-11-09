"""Step answer endpoints — workers fill in answers for scenario steps."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.security import get_current_user
from backend.app.db.session import get_db
from backend.app.models.answer import ObjectAnswer
from backend.app.models.audit import AuditAction
from backend.app.models.comment import StepComment, StepStatusNote
from backend.app.models.notification import NotificationType
from backend.app.models.object import Object, ObjectStatus, ObjectWorker
from backend.app.models.scenario import Scenario
from backend.app.models.user import User, UserRole
from backend.app.services.audit import log_action
from backend.app.services.notifications import notify
from backend.app.schemas.answer import AnswerCreate, AnswerResponse
from backend.app.schemas.error import RESPONSES_CRUD, RESPONSES_CRUD_CONFLICT
from backend.app.schemas.step_comment import StepCommentCreate, StepCommentResponse, StepStatusNoteCreate, StepStatusNoteResponse

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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="На цей крок уже є відповідь")

    answer = ObjectAnswer(
        object_id=object_id,
        step_id=step_id,
        answer_text=data.answer_text,
        answered_by_id=current_user.id,
        is_locked=False,
        comments=[],
    )
    db.add(answer)
    await db.flush()

    await log_action(
        db, user_id=current_user.id, action=AuditAction.CREATE,
        entity_type="answer", entity_id=answer.id, object_id=object_id,
        details={"step_id": step_id},
    )
    return await _load_answer(db, answer.id)


@router.put("/{step_id}/answer", response_model=AnswerResponse, responses=RESPONSES_CRUD)
async def update_answer(
    object_id: int,
    step_id: int,
    data: AnswerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update answer — only if unlocked by admin."""
    await _verify_access(object_id, current_user, db)

    result = await db.execute(
        select(ObjectAnswer)
        .where(ObjectAnswer.object_id == object_id, ObjectAnswer.step_id == step_id)
        .options(selectinload(ObjectAnswer.comments))
    )
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Відповідь не знайдено")

    if answer.is_locked and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Відповідь заблоковано — зверніться до адміністратора")

    answer.answer_text = data.answer_text
    answer.answered_by_id = current_user.id
    await db.flush()

    await log_action(
        db, user_id=current_user.id, action=AuditAction.UPDATE,
        entity_type="answer", entity_id=answer.id, object_id=object_id,
        details={"step_id": step_id},
    )
    return await _load_answer(db, answer.id)


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
        .options(
            selectinload(StepComment.author),
            selectinload(StepComment.recipient),
            selectinload(StepComment.reply_to).selectinload(StepComment.author),
        )
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
        reply_to_id=data.reply_to_id,
        comment_text=data.comment_text,
    )
    db.add(comment)
    await db.flush()

    if data.recipient_id and data.recipient_id != current_user.id:
        await notify(
            db,
            user_id=data.recipient_id,
            notification_type=NotificationType.STEP_COMMENT,
            title="Згадка в обговоренні",
            message=f"{current_user.first_name} згадує вас в обговоренні кроку",
            push_text=f"💬 {current_user.first_name} згадує вас в обговоренні кроку",
            object_id=object_id,
            step_number=step_id,
        )

    await log_action(
        db, user_id=current_user.id, action=AuditAction.COMMENT,
        entity_type="step_comment", entity_id=comment.id, object_id=object_id,
        details={"step_id": step_id, "recipient_id": data.recipient_id},
    )

    result = await db.execute(
        select(StepComment)
        .where(StepComment.id == comment.id)
        .options(
            selectinload(StepComment.author),
            selectinload(StepComment.recipient),
            selectinload(StepComment.reply_to).selectinload(StepComment.author),
        )
    )
    return result.scalar_one()


@router.get("/{step_id}/status-notes", response_model=list[StepStatusNoteResponse], responses=RESPONSES_CRUD)
async def list_status_notes(
    object_id: int,
    step_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List status log entries for a step, oldest first."""
    await _verify_access(object_id, current_user, db)

    result = await db.execute(
        select(StepStatusNote)
        .where(StepStatusNote.object_id == object_id, StepStatusNote.step_id == step_id)
        .options(selectinload(StepStatusNote.author))
        .order_by(StepStatusNote.created_at.asc())
    )
    return result.scalars().all()


@router.post("/{step_id}/status-notes", response_model=StepStatusNoteResponse, status_code=status.HTTP_201_CREATED, responses=RESPONSES_CRUD)
async def add_status_note(
    object_id: int,
    step_id: int,
    data: StepStatusNoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a status update to the step log. Only responsible workers and admins can post."""
    await _verify_access(object_id, current_user, db)

    # Only responsible workers (in object_workers) or admin can post status notes
    if current_user.role != UserRole.ADMIN:
        worker_result = await db.execute(
            select(ObjectWorker).where(
                ObjectWorker.object_id == object_id,
                ObjectWorker.user_id == current_user.id,
            )
        )
        if not worker_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Додавати статус можуть лише відповідальні співробітники")

    # Block if step is locked (unless admin)
    answer_result = await db.execute(
        select(ObjectAnswer).where(ObjectAnswer.object_id == object_id, ObjectAnswer.step_id == step_id)
    )
    answer = answer_result.scalar_one_or_none()
    if answer and answer.is_locked and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Крок заблоковано")

    note = StepStatusNote(
        object_id=object_id,
        step_id=step_id,
        author_id=current_user.id,
        note_text=data.note_text,
    )
    db.add(note)
    await db.flush()

    # Auto-create ObjectAnswer on first note so locking/completion tracking works
    if not answer:
        new_answer = ObjectAnswer(
            object_id=object_id,
            step_id=step_id,
            answer_text="",
            answered_by_id=current_user.id,
            is_locked=False,
            comments=[],
        )
        db.add(new_answer)
        await db.flush()

        # Auto-complete object when last step is answered
        obj_res = await db.execute(
            select(Object)
            .where(Object.id == object_id)
            .options(
                selectinload(Object.scenario).selectinload(Scenario.steps),
                selectinload(Object.workers).selectinload(ObjectWorker.user),
            )
        )
        obj = obj_res.scalar_one_or_none()
        if obj and obj.status != ObjectStatus.COMPLETED:
            count_res = await db.execute(
                select(func.count(ObjectAnswer.id)).where(ObjectAnswer.object_id == object_id)
            )
            answered_count = count_res.scalar()
            total_steps = len(obj.scenario.steps) if obj.scenario else 0
            if total_steps > 0 and answered_count >= total_steps:
                obj.status = ObjectStatus.COMPLETED
                await db.flush()
                await log_action(
                    db, user_id=current_user.id, action=AuditAction.STATUS_CHANGE,
                    entity_type="object", entity_id=object_id, object_id=object_id,
                    details={"status": "completed"},
                )
                for worker_link in obj.workers:
                    await notify(
                        db,
                        user_id=worker_link.user_id,
                        notification_type=NotificationType.OBJECT_COMPLETED,
                        title="Обʼєкт завершено",
                        message=f"Усі кроки обʼєкта '{obj.name}' заповнено",
                        push_text=f"✅ Обʼєкт «{obj.name}» повністю заповнено!",
                        object_id=object_id,
                    )

    await log_action(
        db, user_id=current_user.id, action=AuditAction.CREATE,
        entity_type="step_status_note", entity_id=note.id, object_id=object_id,
        details={"step_id": step_id},
    )

    result = await db.execute(
        select(StepStatusNote)
        .where(StepStatusNote.id == note.id)
        .options(selectinload(StepStatusNote.author))
    )
    return result.scalar_one()


async def _load_answer(db: AsyncSession, answer_id: int) -> ObjectAnswer:
    """Re-fetch answer with all relationships needed for AnswerResponse serialization."""
    result = await db.execute(
        select(ObjectAnswer)
        .where(ObjectAnswer.id == answer_id)
        .options(
            selectinload(ObjectAnswer.comments),
            selectinload(ObjectAnswer.answered_by_user),
        )
    )
    return result.scalar_one()


async def _verify_access(object_id: int, user: User, db: AsyncSession) -> None:
    """Check user has access to object."""
    result = await db.execute(select(Object).where(Object.id == object_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Обʼєкт не знайдено")

    if user.role == UserRole.ADMIN:
        return

    worker = await db.execute(
        select(ObjectWorker).where(ObjectWorker.object_id == object_id, ObjectWorker.user_id == user.id)
    )
    if not worker.scalar_one_or_none() and obj.created_by_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Немає доступу")
