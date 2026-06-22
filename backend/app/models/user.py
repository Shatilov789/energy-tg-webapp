"""User model — workers and administrators."""

import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.mixins import SoftDeleteMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    WORKER = "worker"


class User(SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.WORKER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    created_objects: Mapped[list["Object"]] = relationship(back_populates="creator")
    answers: Mapped[list["ObjectAnswer"]] = relationship(back_populates="answered_by_user")
    comments: Mapped[list["AdminComment"]] = relationship(back_populates="admin")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.id} tg={self.telegram_id} role={self.role.value}>"
