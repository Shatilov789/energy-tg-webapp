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
    object_id: int | None = None
    step_number: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
