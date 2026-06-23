"""StepComment schemas — discussion thread under a scenario step."""

from datetime import datetime

from pydantic import BaseModel

from backend.app.schemas.user import UserBriefResponse


class StepCommentCreate(BaseModel):
    comment_text: str
    recipient_id: int | None = None


class StepCommentResponse(BaseModel):
    id: int
    object_id: int
    step_id: int
    comment_text: str
    created_at: datetime
    author: UserBriefResponse
    recipient: UserBriefResponse | None = None

    model_config = {"from_attributes": True}
