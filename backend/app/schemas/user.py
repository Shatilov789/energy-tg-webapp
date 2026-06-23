"""User schemas."""

from datetime import datetime

from pydantic import BaseModel

from backend.app.models.user import UserRole


class UserCreate(BaseModel):
    telegram_id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    role: UserRole = UserRole.WORKER


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBriefResponse(BaseModel):
    """Minimal user info — colleague picker, comment author/recipient."""

    id: int
    first_name: str
    last_name: str | None
    username: str | None
    role: UserRole

    model_config = {"from_attributes": True}
