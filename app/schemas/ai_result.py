"""
Pydantic schemas for AIResult model.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AIResultResponse(BaseModel):
    """Schema for returning an AIResult."""
    id: UUID
    submission_id: UUID
    score_percent: float
    confidence_score: float
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    raw_response: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
