"""AdminComment model — admin feedback on worker's answers."""

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
