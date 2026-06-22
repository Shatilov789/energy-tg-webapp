"""Authentication endpoints."""

from fastapi import APIRouter, Depends

from backend.app.core.security import get_current_user
from backend.app.models.user import User
from backend.app.schemas.error import RESPONSES_AUTH
from backend.app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserResponse, responses=RESPONSES_AUTH)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user
