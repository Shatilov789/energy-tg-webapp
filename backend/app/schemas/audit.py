"""Audit log schemas."""

from datetime import datetime

from pydantic import BaseModel

from backend.app.models.audit import AuditAction
from backend.app.schemas.user import UserBriefResponse


class AuditLogEntryResponse(BaseModel):
    id: int
    action: AuditAction
    entity_type: str
    entity_id: int | None
    object_id: int | None
    details: str | None
    created_at: datetime
    user: UserBriefResponse | None = None

    model_config = {"from_attributes": True}
