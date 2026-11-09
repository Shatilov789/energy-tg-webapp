"""Deal / Stage schemas."""

from datetime import datetime

from pydantic import BaseModel

from backend.app.models.deal import DealStatus


class StageResponse(BaseModel):
    id: int
    stage_key: str
    display_code: str
    name: str
    role_owner: str
    order_index: int
    is_decision: bool
    yes_label: str | None = None
    no_label: str | None = None

    model_config = {"from_attributes": True}


class DealCreate(BaseModel):
    process_type: str = "СЕС"
    client_name: str
    client_phone: str
    client_email: str | None = None
    object_address: str | None = None
    lead_source: str | None = None


class DealResponse(BaseModel):
    id: int
    process_type: str
    client_name: str
    client_phone: str
    client_email: str | None
    object_address: str | None
    lead_source: str | None
    status: DealStatus
    closure_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DealListItemResponse(DealResponse):
    current_stage_name: str | None = None
    current_stage_code: str | None = None


class DealStageCommentResponse(BaseModel):
    id: int
    author_id: int | None
    comment_text: str
    is_system_event: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DealStageProgressResponse(BaseModel):
    id: int
    stage_id: int
    stage_name: str
    stage_code: str
    is_decision: bool
    yes_label: str | None = None
    no_label: str | None = None
    status: str
    decision: bool | None
    started_at: datetime | None
    completed_at: datetime | None
    comments: list[DealStageCommentResponse] = []

    model_config = {"from_attributes": True}


class DealDetailResponse(DealListItemResponse):
    current_stage_is_decision: bool = False
    active_stages: list[DealStageProgressResponse] = []
    history: list[DealStageProgressResponse] = []


class DealAdvance(BaseModel):
    decision: bool | None = None
    comment: str | None = None
    progress_id: int | None = None
