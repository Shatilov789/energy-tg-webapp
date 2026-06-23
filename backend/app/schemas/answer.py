"""Answer schemas."""

from datetime import datetime

from pydantic import BaseModel

from backend.app.schemas.comment import CommentResponse


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
    comments: list[CommentResponse] = []

    model_config = {"from_attributes": True}
