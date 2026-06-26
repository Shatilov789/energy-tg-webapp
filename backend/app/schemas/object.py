"""Object schemas."""

from datetime import datetime

from pydantic import BaseModel

from backend.app.models.object import ObjectStatus
from backend.app.schemas.answer import AnswerResponse
from backend.app.schemas.scenario import ScenarioResponse, ScenarioWithStepsResponse
from backend.app.schemas.user import UserBriefResponse


class ObjectCreate(BaseModel):
    name: str
    comment: str | None = None
    scenario_id: int


class WorkerResponse(BaseModel):
    """Ответственный за объект — строка таблицы object_workers."""

    id: int
    user_id: int
    user: UserBriefResponse
    added_at: datetime

    model_config = {"from_attributes": True}


class ObjectResponse(BaseModel):
    id: int
    name: str
    comment: str | None
    scenario_id: int
    created_by_id: int
    status: ObjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ObjectDetailResponse(ObjectResponse):
    scenario: ScenarioResponse | None = None
    answers: list[AnswerResponse] = []
    workers: list[WorkerResponse] = []


class ObjectListItemResponse(ObjectResponse):
    """Object enriched with progress meta — avoids N+1 detail fetches on the home screen."""

    scenario_name: str
    total_steps: int
    answered_steps: int
    next_step: int


class AdminObjectResponse(ObjectResponse):
    """Object with full scenario steps + answers + workers — used by admin oversight list."""

    scenario: ScenarioWithStepsResponse | None = None
    answers: list[AnswerResponse] = []
    workers: list[WorkerResponse] = []
