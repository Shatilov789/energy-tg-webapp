"""Object model — inspection target created by a worker."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.mixins import SoftDeleteMixin


class ObjectStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ObjectCriticality(str, enum.Enum):
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Object(SoftDeleteMixin, Base):
    __tablename__ = "objects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    comment: Mapped[str | None] = mapped_column(Text)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id"), index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[ObjectStatus] = mapped_column(Enum(ObjectStatus), default=ObjectStatus.IN_PROGRESS)
    criticality: Mapped[ObjectCriticality] = mapped_column(
        Enum(ObjectCriticality), default=ObjectCriticality.NORMAL
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    scenario: Mapped["Scenario"] = relationship(back_populates="objects")
    creator: Mapped["User"] = relationship(back_populates="created_objects")
    workers: Mapped[list["ObjectWorker"]] = relationship(back_populates="object", cascade="all, delete-orphan")
    answers: Mapped[list["ObjectAnswer"]] = relationship(back_populates="object", cascade="all, delete-orphan")
    step_comments: Mapped[list["StepComment"]] = relationship(back_populates="object", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Object {self.id} '{self.name}' status={self.status.value}>"


class ObjectWorker(Base):
    """Many-to-many: which workers have access to an object."""

    __tablename__ = "object_workers"

    id: Mapped[int] = mapped_column(primary_key=True)
    object_id: Mapped[int] = mapped_column(ForeignKey("objects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    object: Mapped["Object"] = relationship(back_populates="workers")
    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<ObjectWorker object={self.object_id} user={self.user_id}>"
