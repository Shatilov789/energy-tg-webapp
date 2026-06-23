"""Comment models — admin feedback on answers, and worker discussion threads per step."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class AdminComment(Base):
    __tablename__ = "admin_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    answer_id: Mapped[int] = mapped_column(ForeignKey("object_answers.id", ondelete="CASCADE"), index=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    comment_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    answer: Mapped["ObjectAnswer"] = relationship(back_populates="comments")
    admin: Mapped["User"] = relationship(back_populates="comments")

    def __repr__(self) -> str:
        return f"<AdminComment {self.id} answer={self.answer_id}>"


class StepComment(Base):
    """Discussion thread under a scenario step — any worker can post, optionally @-mentioning a colleague."""

    __tablename__ = "step_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    object_id: Mapped[int] = mapped_column(ForeignKey("objects.id", ondelete="CASCADE"), index=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("scenario_steps.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    recipient_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    comment_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    object: Mapped["Object"] = relationship(back_populates="step_comments")
    author: Mapped["User"] = relationship(foreign_keys=[author_id])
    recipient: Mapped["User | None"] = relationship(foreign_keys=[recipient_id])

    def __repr__(self) -> str:
        return f"<StepComment {self.id} object={self.object_id} step={self.step_id}>"
