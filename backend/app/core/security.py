"""Telegram Web App authentication — validates initData from Telegram."""

import hashlib
import hmac
import json
from urllib.parse import parse_qs

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.user import User, UserRole


def validate_telegram_init_data(init_data: str) -> dict | None:
    """Validate Telegram Web App initData hash. Returns parsed user data or None."""
    if not settings.telegram_bot_token:
        return None

    parsed = parse_qs(init_data)
    received_hash = parsed.get("hash", [None])[0]
    if not received_hash:
        return None

    data_check_pairs = []
    for key, values in sorted(parsed.items()):
        if key != "hash":
            data_check_pairs.append(f"{key}={values[0]}")
    data_check_string = "\n".join(data_check_pairs)

    secret_key = hmac.new(b"WebAppData", settings.telegram_bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    user_data = parsed.get("user", [None])[0]
    if user_data:
        return json.loads(user_data)
    return None


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """FastAPI dependency: extract and validate current user from TG initData."""
    init_data = request.headers.get("X-Telegram-Init-Data", "")

    # Dev mode: allow header-based auth bypass
    if settings.is_development:
        dev_tg_id = request.headers.get("X-Dev-Telegram-Id")
        if dev_tg_id:
            result = await db.execute(select(User).where(User.telegram_id == int(dev_tg_id)))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            return user

    user_data = validate_telegram_init_data(init_data)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram auth")

    telegram_id = user_data["id"]
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not registered")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User deactivated")

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: require admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
