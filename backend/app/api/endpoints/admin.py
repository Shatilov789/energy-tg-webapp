"""Admin endpoints — manage users, view all objects, comment, unlock answers."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.security import require_admin
from backend.app.db.session import get_db
from backend.app.models.answer import ObjectAnswer
from backend.app.models.audit import AuditAction
from backend.app.models.comment import AdminComment
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.object import Object
from backend.app.models.user import User, UserRole
from backend.app.services.audit import log_action
from backend.app.schemas.comment import CommentCreate, CommentResponse
from backend.app.schemas.error import RESPONSES_AUTH, RESPONSES_CRUD, RESPONSES_CRUD_CONFLICT
from backend.app.schemas.user import UserCreate, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# --- User management ---


@router.get("/users", response_model=list[UserResponse], responses=RESPONSES_AUTH)
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all registered users."""
    result = await db.execute(
        select(User).where(User.is_deleted.is_(False)).order_by(User.created_at.desc())
    )
    return result.scalars().all()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, responses=RESPONSES_CRUD_CONFLICT)
async def create_user(
    data: UserCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Register new user by Telegram ID."""
    existing = await db.execute(select(User).where(User.telegram_id == data.telegram_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

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
        db, user_id=admin.id, action=AuditAction.CREATE,
        entity_type="user", entity_id=user.id,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = not user.is_active
    await db.flush()
    await log_action(
        db, user_id=admin.id, action=AuditAction.STATUS_CHANGE,
        entity_type="user", entity_id=user_id,
        details={"is_active": user.is_active},
    )
    return user


# --- Object oversight ---


@router.get("/objects", response_model=list, responses=RESPONSES_AUTH)
async def list_all_objects(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all objects across all workers."""
    result = await db.execute(
        select(Object).options(selectinload(Object.scenario), selectinload(Object.creator)).order_by(
            Object.updated_at.desc()
        )
    )
    return result.scalars().all()


# --- Comments ---


@router.post("/answers/{answer_id}/comment", response_model=CommentResponse, status_code=status.HTTP_201_CREATED, responses=RESPONSES_CRUD)
async def add_comment(
    answer_id: int,
    data: CommentCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add admin comment to an answer — sends notification to worker."""
    result = await db.execute(
        select(ObjectAnswer).where(ObjectAnswer.id == answer_id).options(selectinload(ObjectAnswer.object))
    )
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")

    comment = AdminComment(answer_id=answer_id, admin_id=admin.id, comment_text=data.comment_text)
    db.add(comment)

    notification = Notification(
        user_id=answer.answered_by_id,
        type=NotificationType.ADMIN_COMMENT,
        title="New comment from admin",
        message=f"Admin commented on step in '{answer.object.name}'",
    )
    db.add(notification)
    await db.flush()

    await log_action(
        db, user_id=admin.id, action=AuditAction.COMMENT,
        entity_type="answer", entity_id=answer_id,
    )
    return comment


# --- Unlock answers ---


@router.patch("/answers/{answer_id}/unlock", responses=RESPONSES_CRUD)
async def unlock_answer(
    answer_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Unlock answer so worker can edit it."""
    result = await db.execute(select(ObjectAnswer).where(ObjectAnswer.id == answer_id))
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")

    answer.is_locked = False
    await db.flush()

    notification = Notification(
        user_id=answer.answered_by_id,
        type=NotificationType.STEP_UNLOCKED,
        title="Step unlocked",
        message=f"Admin unlocked a step for editing",
    )
    db.add(notification)
    await db.flush()

    await log_action(
        db, user_id=admin.id, action=AuditAction.UNLOCK,
        entity_type="answer", entity_id=answer_id,
    )
    return {"detail": "Answer unlocked"}
