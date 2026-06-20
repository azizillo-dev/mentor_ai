"""
Pydantic schemas for Group model.
Pydantic v2 ishlatilgan.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GroupBase(BaseModel):
    """Base fields for Group."""
    name: str = Field(..., max_length=255, description="Guruh nomi")
    subject: str | None = Field(None, max_length=255, description="Fan nomi (ixtiyoriy)")


class GroupCreate(GroupBase):
    """Schema for creating a group."""
    pass


class GroupUpdate(BaseModel):
    """Schema for updating a group."""
    name: str | None = Field(None, max_length=255)
    subject: str | None = Field(None, max_length=255)


class GroupResponse(GroupBase):
    """Schema for returning a group."""
    id: UUID
    teacher_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
