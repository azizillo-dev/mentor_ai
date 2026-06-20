"""
User Pydantic schemas for request/response validation.
"""

from datetime import datetime

from pydantic import EmailStr, Field

from app.models.user import UserRole
from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    """Shared user fields."""

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.STUDENT


class UserResponse(UserBase):
    """
    Public user representation returned from API endpoints.
    Never includes sensitive fields like hashed_password.
    """

    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseSchema):
    """Fields allowed for user profile updates."""

    full_name: str | None = Field(None, min_length=2, max_length=255)
