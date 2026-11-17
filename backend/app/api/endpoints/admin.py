"""Admin endpoints — manage users."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import require_admin
from backend.app.db.session import get_db
from backend.app.models.audit import AuditAction
from backend.app.models.user import User
from backend.app.schemas.error import RESPONSES_AUTH, RESPONSES_CRUD, RESPONSES_CRUD_CONFLICT, ErrorResponse
from backend.app.schemas.user import UserCreate, UserResponse
from backend.app.services.audit import log_action

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


@router.patch(
    "/users/{user_id}/toggle-active",
    response_model=UserResponse,
    responses={**RESPONSES_CRUD, 400: {"model": ErrorResponse, "description": "Cannot deactivate yourself"}},
)
async def toggle_user_active(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate user."""
    # Locking yourself out leaves no admin to undo it except a manual database fix.
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не можна деактивувати себе")
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
