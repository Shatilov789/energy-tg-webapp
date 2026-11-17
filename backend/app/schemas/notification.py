"""Notification schemas."""

from datetime import datetime

from pydantic import BaseModel

from backend.app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    id: int
    type: NotificationType
    title: str
    message: str
    is_read: bool
    deal_id: int | None = None
    progress_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
