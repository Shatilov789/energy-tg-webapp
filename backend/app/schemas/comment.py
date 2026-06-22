"""Comment schemas."""

from datetime import datetime

from pydantic import BaseModel


class CommentCreate(BaseModel):
    comment_text: str


class CommentResponse(BaseModel):
    id: int
    answer_id: int
    admin_id: int
    comment_text: str
    created_at: datetime

    model_config = {"from_attributes": True}
