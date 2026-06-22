"""Scenario schemas."""

from datetime import datetime

from pydantic import BaseModel


class ScenarioCreate(BaseModel):
    name: str
    description: str | None = None


class ScenarioResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ScenarioStepCreate(BaseModel):
    step_number: int
    question_text: str
    description: str | None = None
    is_required: bool = True


class ScenarioStepResponse(BaseModel):
    id: int
    scenario_id: int
    step_number: int
    question_text: str
    description: str | None
    is_required: bool

    model_config = {"from_attributes": True}


class ScenarioWithStepsResponse(ScenarioResponse):
    steps: list[ScenarioStepResponse] = []
