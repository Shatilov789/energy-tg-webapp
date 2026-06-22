"""ObjectAnswer model — worker's answer to a scenario step."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.mixins import SoftDeleteMixin


class ObjectAnswer(SoftDeleteMixin, Base):
    __tablename__ = "object_answers"

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
