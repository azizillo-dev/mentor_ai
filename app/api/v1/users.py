"""
User endpoints: profile retrieval and management.
"""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DBSession
from app.schemas.base import SuccessResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Get current user profile",
    description="Returns the authenticated user's profile data.",
)
async def get_me(current_user: CurrentUser) -> SuccessResponse[UserResponse]:
    """Retrieve the currently authenticated user's profile."""
    return SuccessResponse(
        message="Profile retrieved successfully",
        data=UserResponse.model_validate(current_user),
    )


@router.patch(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Update current user profile",
    description="Update the authenticated user's profile (full_name only at this stage).",
)
async def update_me(
    payload: UserUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> SuccessResponse[UserResponse]:
    """Update the authenticated user's profile fields."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
        await db.flush()
        await db.refresh(current_user)

    return SuccessResponse(
        message="Profile updated successfully",
        data=UserResponse.model_validate(current_user),
    )
