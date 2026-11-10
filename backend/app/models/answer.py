"""ObjectAnswer model — worker's answer to a scenario step."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.mixins import SoftDeleteMixin


class ObjectAnswer(SoftDeleteMixin, Base):
    __tablename__ = "object_answers"
    # One live answer per step of an object; soft-deleted rows do not count.
    __table_args__ = (
        Index(
            "uq_object_answers_object_step_active",
            "object_id",
            "step_id",
            unique=True,
            postgresql_where=text("is_deleted = false"),
            sqlite_where=text("is_deleted = 0"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    object_id: Mapped[int] = mapped_column(ForeignKey("objects.id", ondelete="CASCADE"), index=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("scenario_steps.id"), index=True)
    answer_text: Mapped[str] = mapped_column(Text)
    answered_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=True)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    object: Mapped["Object"] = relationship(back_populates="answers")
    step: Mapped["ScenarioStep"] = relationship(back_populates="answers")
    answered_by_user: Mapped["User"] = relationship(back_populates="answers")
    comments: Mapped[list["AdminComment"]] = relationship(back_populates="answer", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ObjectAnswer {self.id} object={self.object_id} step={self.step_id}>"
