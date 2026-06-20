"""
Pydantic schemas for Homework model.
Pydantic v2 ishlatilgan.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HomeworkBase(BaseModel):
    """Base fields for Homework."""
    title: str = Field(..., max_length=255, description="Uy vazifasi sarlavhasi")
    description: str | None = Field(None, description="Uy vazifasi ta'rifi (ixtiyoriy)")
    deadline: datetime = Field(..., description="Topshirish muddati")


class HomeworkCreate(HomeworkBase):
    """Schema for creating a homework."""
    group_id: UUID = Field(..., description="Tegishli guruh ID si")


class HomeworkUpdate(BaseModel):
    """Schema for updating a homework."""
    title: str | None = Field(None, max_length=255)
    description: str | None = Field(None)
    deadline: datetime | None = Field(None)


class HomeworkResponse(HomeworkBase):
    """Schema for returning a homework."""
    id: UUID
    group_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
