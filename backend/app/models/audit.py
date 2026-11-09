"""AuditLog model — tracks all significant actions in the system."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    UNLOCK = "unlock"
    SHARE = "share"
    COMMENT = "comment"
    LOGIN = "login"
    STATUS_CHANGE = "status_change"
    CRITICALITY_CHANGE = "criticality_change"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), index=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer)
    object_id: Mapped[int | None] = mapped_column(ForeignKey("objects.id"), index=True)
    deal_id: Mapped[int | None] = mapped_column(ForeignKey("deals.id"), index=True)
    details: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped["User | None"] = relationship("User", foreign_keys="[AuditLog.user_id]", viewonly=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.id} {self.action.value} {self.entity_type}:{self.entity_id}>"
