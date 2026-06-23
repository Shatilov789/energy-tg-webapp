"""User directory — colleague picker for step discussions."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.user import UserBriefResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserBriefResponse])
async def list_colleagues(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List active users available as discussion colleagues (excluding self)."""
    result = await db.execute(
        select(User)
        .where(
            User.is_deleted.is_(False),
            User.is_active.is_(True),
            User.id != current_user.id,
        )
        .order_by(User.first_name)
    )
    return result.scalars().all()
