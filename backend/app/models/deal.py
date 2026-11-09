"""Business process models: Deal, Stage catalog, DealStageProgress, DealStageComment.

Multi-role handoff pipeline (12 roles), separate from Object/ScenarioStep (single-worker inspections).
Each process is defined in backend/app/processes/.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class DealStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    COMPLETED = "completed"


class StageStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    SKIPPED = "skipped"


class PaymentContext(str, enum.Enum):
    DESIGN_FEE = "design_fee"
    INSTALLATION_FEE = "installation_fee"


class Stage(Base):
    """Catalog of process stages — seeded once per process, referenced by DealStageProgress."""

    __tablename__ = "stages"

    id: Mapped[int] = mapped_column(primary_key=True)
    stage_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    display_code: Mapped[str] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(255))
    role_owner: Mapped[str] = mapped_column(String(100))
    order_index: Mapped[int] = mapped_column(Integer, index=True)
    is_decision: Mapped[bool] = mapped_column(Boolean, default=False)
    yes_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    no_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parent_process: Mapped[str] = mapped_column(String(50), default="СЕС")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Stage {self.id} {self.stage_key} '{self.name}'>"


class Deal(Base):
    """A deal: moves through its process's Stage catalog via DealStageProgress rows."""

    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(primary_key=True)
    process_type: Mapped[str] = mapped_column(String(50), default="СЕС")
    client_name: Mapped[str] = mapped_column(String(255))
    client_phone: Mapped[str] = mapped_column(String(50))
    client_email: Mapped[str | None] = mapped_column(String(255))
    object_address: Mapped[str | None] = mapped_column(String(255))
    lead_source: Mapped[str | None] = mapped_column(String(100))
    current_stage_id: Mapped[int | None] = mapped_column(ForeignKey("stages.id"), index=True)
    status: Mapped[DealStatus] = mapped_column(Enum(DealStatus), default=DealStatus.ACTIVE)
    closure_reason: Mapped[str | None] = mapped_column(String(255))
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    current_stage: Mapped["Stage | None"] = relationship()
    creator: Mapped["User"] = relationship()
    progress: Mapped[list["DealStageProgress"]] = relationship(
        back_populates="deal", cascade="all, delete-orphan", order_by="DealStageProgress.created_at"
    )

    def __repr__(self) -> str:
        return f"<Deal {self.id} '{self.client_name}' status={self.status.value}>"


class DealStageProgress(Base):
    """One visit to a stage by a deal. No unique(deal_id, stage_id) — loops create new rows."""

    __tablename__ = "deal_stage_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"), index=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id"), index=True)
    status: Mapped[StageStatus] = mapped_column(Enum(StageStatus), default=StageStatus.PENDING)
    decision: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    payment_context: Mapped[PaymentContext | None] = mapped_column(Enum(PaymentContext), nullable=True)
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    deal: Mapped["Deal"] = relationship(back_populates="progress")
    stage: Mapped["Stage"] = relationship()
    assigned_user: Mapped["User | None"] = relationship()
    comments: Mapped[list["DealStageComment"]] = relationship(back_populates="progress", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<DealStageProgress {self.id} deal={self.deal_id} stage={self.stage_id}>"


class DealStageComment(Base):
    """Discussion thread on a deal stage visit — mirrors StepComment's shape."""

    __tablename__ = "deal_stage_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_stage_progress_id: Mapped[int] = mapped_column(
        ForeignKey("deal_stage_progress.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    recipient_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    reply_to_id: Mapped[int | None] = mapped_column(ForeignKey("deal_stage_comments.id"), nullable=True)
    comment_text: Mapped[str] = mapped_column(Text)
    is_system_event: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    event_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    progress: Mapped["DealStageProgress"] = relationship(back_populates="comments")
    author: Mapped["User | None"] = relationship(foreign_keys=[author_id])
    recipient: Mapped["User | None"] = relationship(foreign_keys=[recipient_id])
    reply_to: Mapped["DealStageComment | None"] = relationship(
        "DealStageComment", foreign_keys=[reply_to_id], remote_side=[id], uselist=False
    )

    def __repr__(self) -> str:
        return f"<DealStageComment {self.id} progress={self.deal_stage_progress_id}>"
