"""StepComment and StepStatusNote schemas."""

from datetime import datetime

from pydantic import BaseModel

from backend.app.schemas.user import UserBriefResponse


class StepCommentCreate(BaseModel):
    comment_text: str
    recipient_id: int | None = None
    reply_to_id: int | None = None


class StepCommentBrief(BaseModel):
    """Nested view used inside reply_to — one level only, no further nesting."""

    id: int
    comment_text: str
    is_system_event: bool = False
    event_type: str | None = None
    author: UserBriefResponse | None = None

    model_config = {"from_attributes": True}


class StepCommentResponse(BaseModel):
    id: int
    object_id: int
    step_id: int
    comment_text: str
    is_system_event: bool = False
    event_type: str | None = None
    reply_to_id: int | None = None
    reply_to: StepCommentBrief | None = None
    created_at: datetime
    author: UserBriefResponse | None = None
    recipient: UserBriefResponse | None = None

    model_config = {"from_attributes": True}


class StepStatusNoteCreate(BaseModel):
    note_text: str


class StepStatusNoteResponse(BaseModel):
    id: int
    object_id: int
    step_id: int
    note_text: str
    created_at: datetime
    author: UserBriefResponse

    model_config = {"from_attributes": True}
