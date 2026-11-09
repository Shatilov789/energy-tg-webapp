"""Scenario and ScenarioStep models — define inspection workflows."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.db.mixins import SoftDeleteMixin


class Scenario(SoftDeleteMixin, Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    steps: Mapped[list["ScenarioStep"]] = relationship(back_populates="scenario", order_by="ScenarioStep.step_number")
    objects: Mapped[list["Object"]] = relationship(back_populates="scenario")

    def __repr__(self) -> str:
        return f"<Scenario {self.id} '{self.name}'>"


class ScenarioStep(Base):
    __tablename__ = "scenario_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)
    step_number: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    scenario: Mapped["Scenario"] = relationship(back_populates="steps")
    answers: Mapped[list["ObjectAnswer"]] = relationship(back_populates="step")

    def __repr__(self) -> str:
        return f"<ScenarioStep {self.id} scenario={self.scenario_id} #{self.step_number}>"
