"""Notification model — reminders and admin comment alerts."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class NotificationType(str, enum.Enum):
    REMINDER = "reminder"
    ADMIN_COMMENT = "admin_comment"
    OBJECT_SHARED = "object_shared"
    STEP_UNLOCKED = "step_unlocked"
    STEP_COMMENT = "step_comment"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    object_id: Mapped[int | None] = mapped_column(ForeignKey("objects.id", ondelete="SET NULL"), nullable=True)
    step_number: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification {self.id} user={self.user_id} type={self.type.value}>"
