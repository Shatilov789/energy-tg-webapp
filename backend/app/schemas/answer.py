"""Answer schemas."""

from datetime import datetime

from pydantic import BaseModel


class AnswerCreate(BaseModel):
    answer_text: str


class AnswerResponse(BaseModel):
    id: int
    object_id: int
    step_id: int
    answer_text: str
    answered_by_id: int
    is_locked: bool
    answered_at: datetime

    model_config = {"from_attributes": True}
