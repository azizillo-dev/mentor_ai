"""
Authentication endpoints: /register, /login.
"""

from fastapi import APIRouter

from app.api.deps import DBSession
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.schemas.base import SuccessResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=SuccessResponse[RegisterResponse],
    status_code=201,
    summary="Register a new user",
    description="Create a new teacher or student account. Returns user data and JWT access token.",
)
async def register(
    payload: RegisterRequest,
    db: DBSession,
) -> SuccessResponse[RegisterResponse]:
    """Register endpoint — open to all, no authentication required."""
    user, token = await AuthService.register(db, payload)

    return SuccessResponse(
        message="Account created successfully",
        data=RegisterResponse(
            user=UserResponse.model_validate(user),
            token=token,
        ),
    )


@router.post(
    "/login",
    response_model=SuccessResponse[LoginResponse],
    summary="Login",
    description="Authenticate with email and password. Returns user data and JWT access token.",
)
async def login(
    payload: LoginRequest,
    db: DBSession,
) -> SuccessResponse[LoginResponse]:
    """Login endpoint — open to all, no authentication required."""
    user, token = await AuthService.login(db, payload)

    return SuccessResponse(
        message="Login successful",
        data=LoginResponse(
            user=UserResponse.model_validate(user),
            token=token,
        ),
    )
