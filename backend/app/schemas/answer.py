"""Answer schemas."""

from datetime import datetime

from pydantic import BaseModel

from backend.app.schemas.comment import CommentResponse
from backend.app.schemas.user import UserBriefResponse


class AnswerCreate(BaseModel):
    answer_text: str


class AnswerResponse(BaseModel):
    id: int
    object_id: int
    step_id: int
    answer_text: str
    answered_by_id: int
    answered_by_user: UserBriefResponse | None = None
    is_locked: bool
    answered_at: datetime
    updated_at: datetime
    comments: list[CommentResponse] = []

    model_config = {"from_attributes": True}
