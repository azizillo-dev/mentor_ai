"""
Pydantic schemas for Submission model.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.submission import SubmissionStatus


class SubmissionResponse(BaseModel):
    """Schema for returning a submission. Excludes file_path as per requirements."""
    id: UUID
    homework_id: UUID
    student_id: int
    status: SubmissionStatus
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)
