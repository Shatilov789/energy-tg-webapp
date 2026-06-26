"""Comment models — admin feedback on answers, and worker discussion threads per step."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
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
    """Discussion thread under a scenario step.

    Two kinds of entries share this table:
    - User messages (is_system_event=False): posted by workers/admins, support reply chains and @mentions.
    - System events (is_system_event=True): auto-generated on lock/unlock/admin-comment; author_id may be null.
    """

    __tablename__ = "step_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    object_id: Mapped[int] = mapped_column(ForeignKey("objects.id", ondelete="CASCADE"), index=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("scenario_steps.id", ondelete="CASCADE"), index=True)
    # Nullable for system events (no human author)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    recipient_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    reply_to_id: Mapped[int | None] = mapped_column(ForeignKey("step_comments.id"), nullable=True)
    comment_text: Mapped[str] = mapped_column(Text)
    is_system_event: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # lock | unlock | admin_comment — set only when is_system_event=True
    event_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    object: Mapped["Object"] = relationship(back_populates="step_comments")
    author: Mapped["User | None"] = relationship(foreign_keys=[author_id])
    recipient: Mapped["User | None"] = relationship(foreign_keys=[recipient_id])
    # Self-referential many-to-one: грузим РОДИТЕЛЯ (WHERE id = self.reply_to_id)
    # remote_side=[id] указывает что id — удалённая (родительская) сторона
    reply_to: Mapped["StepComment | None"] = relationship(
        "StepComment",
        foreign_keys=[reply_to_id],
        remote_side=[id],
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<StepComment {self.id} object={self.object_id} step={self.step_id} sys={self.is_system_event}>"


class StepStatusNote(Base):
    """Immutable status log entries for a step — who wrote what and when, append-only."""

    __tablename__ = "step_status_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    object_id: Mapped[int] = mapped_column(ForeignKey("objects.id", ondelete="CASCADE"), index=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("scenario_steps.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    note_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    author: Mapped["User"] = relationship(foreign_keys=[author_id])

    def __repr__(self) -> str:
        return f"<StepStatusNote {self.id} object={self.object_id} step={self.step_id}>"
