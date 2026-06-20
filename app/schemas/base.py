"""
Base Pydantic schemas used across the application.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class BaseSchema(BaseModel):
    """Base schema with common Pydantic configuration."""

    model_config = {
        "from_attributes": True,       # Allow ORM model instances as input
        "populate_by_name": True,      # Allow both alias and field name
        "str_strip_whitespace": True,  # Auto-strip whitespace from strings
    }


class SuccessResponse(BaseSchema, Generic[DataT]):
    """
    Generic success response wrapper.

    Usage:
        return SuccessResponse(data=user, message="User created")
    """

    success: bool = True
    message: str = "OK"
    data: DataT | None = None


class ErrorResponse(BaseSchema):
    """Standard error response format."""

    success: bool = False
    message: str
    detail: Any | None = None


class PaginatedResponse(BaseSchema, Generic[DataT]):
    """Paginated list response."""

    success: bool = True
    data: list[DataT]
    total: int
    page: int
    per_page: int
    pages: int
