"""
Authentication Pydantic schemas: Register, Login, Token responses.
"""

from pydantic import EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.base import BaseSchema
from app.schemas.user import UserResponse


class RegisterRequest(BaseSchema):
    """Request body for user registration."""

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.STUDENT

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Enforce basic password strength requirements.
        - At least 8 characters (enforced by Field min_length)
        - Must contain at least one digit
        - Must contain at least one letter
        """
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        return v


class LoginRequest(BaseSchema):
    """Request body for user login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseSchema):
    """JWT token response returned after successful login or register."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration


class RegisterResponse(BaseSchema):
    """Registration success response."""

    user: UserResponse
    token: TokenResponse


class LoginResponse(BaseSchema):
    """Login success response."""

    user: UserResponse
    token: TokenResponse
