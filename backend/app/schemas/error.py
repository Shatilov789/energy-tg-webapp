"""Unified error response schemas for OpenAPI docs."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str

    model_config = {
        "json_schema_extra": {
            "examples": [{"detail": "Resource not found"}],
        }
    }


# Pre-built response dicts for use in endpoint `responses=` parameter
RESPONSES_401 = {401: {"model": ErrorResponse, "description": "Not authenticated"}}
RESPONSES_403 = {403: {"model": ErrorResponse, "description": "Forbidden"}}
RESPONSES_404 = {404: {"model": ErrorResponse, "description": "Not found"}}
RESPONSES_409 = {409: {"model": ErrorResponse, "description": "Conflict"}}

RESPONSES_AUTH = {**RESPONSES_401, **RESPONSES_403}
RESPONSES_CRUD = {**RESPONSES_401, **RESPONSES_403, **RESPONSES_404}
RESPONSES_CRUD_CONFLICT = {**RESPONSES_CRUD, **RESPONSES_409}
