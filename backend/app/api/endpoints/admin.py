"""Admin endpoints — manage users, view all objects, comment, unlock answers."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.security import require_admin
from backend.app.db.session import get_db
from backend.app.models.answer import ObjectAnswer
from backend.app.models.audit import AuditAction
from backend.app.models.comment import AdminComment, StepComment
from backend.app.models.notification import NotificationType
from backend.app.models.object import Object, ObjectCriticality, ObjectWorker
from backend.app.models.scenario import Scenario
from backend.app.models.user import User
from backend.app.schemas.comment import CommentCreate, CommentResponse
from backend.app.schemas.error import RESPONSES_AUTH, RESPONSES_CRUD, RESPONSES_CRUD_CONFLICT
from backend.app.schemas.object import AdminObjectResponse
from backend.app.schemas.user import UserCreate, UserResponse
from backend.app.services.audit import log_action
from backend.app.services.notifications import notify

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# --- User management ---


@router.get("/users", response_model=list[UserResponse], responses=RESPONSES_AUTH)
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all registered users."""
    result = await db.execute(select(User).where(User.is_deleted.is_(False)).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.post(
    "/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, responses=RESPONSES_CRUD_CONFLICT
)
async def create_user(
    data: UserCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Register new user by Telegram ID."""
    existing = await db.execute(select(User).where(User.telegram_id == data.telegram_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Користувач уже існує")

    user = User(
        telegram_id=data.telegram_id,
        first_name=data.first_name,
        last_name=data.last_name,
        username=data.username,
        role=data.role,
    )
    db.add(user)
    await db.flush()
    await log_action(
        db,
        user_id=admin.id,
        action=AuditAction.CREATE,
        entity_type="user",
        entity_id=user.id,
        details={"telegram_id": data.telegram_id, "role": data.role.value},
    )
    return user


@router.patch("/users/{user_id}/toggle-active", response_model=UserResponse, responses=RESPONSES_CRUD)
async def toggle_user_active(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Користувача не знайдено")
    user.is_active = not user.is_active
    await db.flush()
    await log_action(
        db,
        user_id=admin.id,
        action=AuditAction.STATUS_CHANGE,
        entity_type="user",
        entity_id=user_id,
        details={"is_active": user.is_active},
    )
    return user


# --- Object oversight ---


@router.get("/objects", response_model=list[AdminObjectResponse], responses=RESPONSES_AUTH)
async def list_all_objects(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all objects across all workers."""
    result = await db.execute(
        select(Object)
        .options(
            selectinload(Object.scenario).selectinload(Scenario.steps),
            selectinload(Object.answers.and_(ObjectAnswer.is_deleted.is_(False))).selectinload(ObjectAnswer.comments),
            selectinload(Object.answers.and_(ObjectAnswer.is_deleted.is_(False))).selectinload(
                ObjectAnswer.answered_by_user
            ),
            selectinload(Object.workers).selectinload(ObjectWorker.user),
        )
        .order_by(Object.updated_at.desc())
    )
    _crit_rank = {ObjectCriticality.CRITICAL: 0, ObjectCriticality.HIGH: 1, ObjectCriticality.NORMAL: 2}
    return sorted(
        result.scalars().all(),
        key=lambda o: (_crit_rank.get(o.criticality, 2), -o.updated_at.timestamp()),
    )


# --- Responsible workers ---


@router.post(
    "/objects/{object_id}/workers/{user_id}", status_code=status.HTTP_201_CREATED, responses=RESPONSES_CRUD_CONFLICT
)
async def add_worker(
    object_id: int,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Assign a responsible worker to an object."""
    obj = await db.get(Object, object_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Обʼєкт не знайдено")

    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Користувача не знайдено")

    existing = await db.execute(
        select(ObjectWorker).where(ObjectWorker.object_id == object_id, ObjectWorker.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Користувач уже відповідальний")

    db.add(ObjectWorker(object_id=object_id, user_id=user_id))
    try:
        await db.flush()
    except IntegrityError:
        # Lost a race with a parallel assignment of the same worker.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Користувач уже відповідальний") from None
    await notify(
        db,
        user_id=user_id,
        notification_type=NotificationType.WORKER_ASSIGNED,
        title="Призначено відповідальним",
        message=f"Вас призначено відповідальним за обʼєкт '{obj.name}'",
        push_text=f"🔔 Вас призначено відповідальним за обʼєкт «{obj.name}»",
        object_id=object_id,
    )
    await log_action(
        db,
        user_id=admin.id,
        action=AuditAction.SHARE,
        entity_type="object",
        entity_id=object_id,
        object_id=object_id,
        details={"added_worker": user_id},
    )
    return {"detail": "Worker added"}


@router.delete("/objects/{object_id}/workers/{user_id}", responses=RESPONSES_CRUD)
async def remove_worker(
    object_id: int,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a responsible worker from an object."""
    result = await db.execute(
        select(ObjectWorker).where(ObjectWorker.object_id == object_id, ObjectWorker.user_id == user_id)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Співробітника на обʼєкті не знайдено")

    removed_obj = await db.get(Object, object_id)
    object_label = removed_obj.name if removed_obj else object_id

    await db.delete(link)
    await notify(
        db,
        user_id=user_id,
        notification_type=NotificationType.WORKER_REMOVED,
        title="Знято з обʼєкта",
        message=f"Вас знято з відповідальності за обʼєкт '{object_label}'",
        push_text=f"ℹ️ Вас знято з відповідальності за обʼєкт «{object_label}»",
        object_id=object_id,
    )
    await log_action(
        db,
        user_id=admin.id,
        action=AuditAction.UPDATE,
        entity_type="object",
        entity_id=object_id,
        object_id=object_id,
        details={"removed_worker": user_id},
    )
    return {"detail": "Worker removed"}


# --- Comments ---


@router.post(
    "/answers/{answer_id}/comment",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    responses=RESPONSES_CRUD,
)
async def add_comment(
    answer_id: int,
    data: CommentCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add admin comment to an answer — sends notification to worker."""
    result = await db.execute(
        select(ObjectAnswer)
        .where(ObjectAnswer.id == answer_id)
        .options(selectinload(ObjectAnswer.object), selectinload(ObjectAnswer.step))
    )
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Відповідь не знайдено")

    comment = AdminComment(answer_id=answer_id, admin_id=admin.id, comment_text=data.comment_text)
    db.add(comment)

    # System event in the step's discussion thread
    db.add(
        StepComment(
            object_id=answer.object_id,
            step_id=answer.step_id,
            author_id=admin.id,
            is_system_event=True,
            event_type="admin_comment",
            comment_text="Адміністратор залишив коментар",
        )
    )

    await notify(
        db,
        user_id=answer.answered_by_id,
        notification_type=NotificationType.ADMIN_COMMENT,
        title="Коментар адміністратора",
        message=f"Адміністратор залишив коментар до кроку {answer.step.step_number} в '{answer.object.name}'",
        push_text=f"💬 Адміністратор залишив коментар до кроку {answer.step.step_number} в «{answer.object.name}»",
        object_id=answer.object_id,
        step_number=answer.step.step_number,
    )

    await log_action(
        db,
        user_id=admin.id,
        action=AuditAction.COMMENT,
        entity_type="answer",
        entity_id=answer_id,
        object_id=answer.object_id,
    )
    return comment


# --- Unlock answers ---


@router.patch("/answers/{answer_id}/lock", responses=RESPONSES_CRUD)
async def lock_answer(
    answer_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lock answer so worker cannot edit it until unlocked."""
    result = await db.execute(
        select(ObjectAnswer)
        .where(ObjectAnswer.id == answer_id)
        .options(selectinload(ObjectAnswer.object), selectinload(ObjectAnswer.step))
    )
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Відповідь не знайдено")

    answer.is_locked = True
    await db.flush()

    db.add(
        StepComment(
            object_id=answer.object_id,
            step_id=answer.step_id,
            author_id=None,
            is_system_event=True,
            event_type="lock",
            comment_text="Адміністратор заблокував відповідь",
        )
    )

    await notify(
        db,
        user_id=answer.answered_by_id,
        notification_type=NotificationType.STEP_UNLOCKED,
        title="Крок заблоковано",
        message=f"Адміністратор заблокував крок {answer.step.step_number} в '{answer.object.name}'",
        push_text=f"🔒 Крок {answer.step.step_number} обʼєкта «{answer.object.name}» заблоковано адміністратором",
        object_id=answer.object_id,
        step_number=answer.step.step_number,
    )

    await log_action(
        db,
        user_id=admin.id,
        action=AuditAction.UPDATE,
        entity_type="answer",
        entity_id=answer_id,
        object_id=answer.object_id,
        details={"locked": True},
    )
    return {"detail": "Answer locked"}


@router.patch("/answers/{answer_id}/unlock", responses=RESPONSES_CRUD)
async def unlock_answer(
    answer_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Unlock answer so worker can edit it."""
    result = await db.execute(
        select(ObjectAnswer)
        .where(ObjectAnswer.id == answer_id)
        .options(selectinload(ObjectAnswer.object), selectinload(ObjectAnswer.step))
    )
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Відповідь не знайдено")

    answer.is_locked = False
    await db.flush()

    # System event in the step's discussion thread
    db.add(
        StepComment(
            object_id=answer.object_id,
            step_id=answer.step_id,
            author_id=None,
            is_system_event=True,
            event_type="unlock",
            comment_text="Адміністратор розблокував відповідь",
        )
    )

    await notify(
        db,
        user_id=answer.answered_by_id,
        notification_type=NotificationType.STEP_UNLOCKED,
        title="Крок розблоковано",
        message=f"Адміністратор розблокував крок {answer.step.step_number} в '{answer.object.name}' для редагування",
        push_text=f"🔓 Крок {answer.step.step_number} обʼєкта «{answer.object.name}» розблоковано — можна доповнити",
        object_id=answer.object_id,
        step_number=answer.step.step_number,
    )

    await log_action(
        db,
        user_id=admin.id,
        action=AuditAction.UNLOCK,
        entity_type="answer",
        entity_id=answer_id,
        object_id=answer.object_id,
    )
    return {"detail": "Answer unlocked"}
