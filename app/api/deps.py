"""
FastAPI dependency injection functions.
Centralizes all shared dependencies: database session, current user, role guards.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenException,
    InvalidTokenException,
    UserNotFoundException,
)
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.user_service import UserService

# ─── Security Scheme ──────────────────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=True)

# ─── Type Aliases ─────────────────────────────────────────────────────────────
DBSession = Annotated[AsyncSession, Depends(get_db)]
BearerToken = Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]


async def get_current_user(
    credentials: BearerToken,
    db: DBSession,
) -> User:
    """
    Dependency: Validates JWT Bearer token and returns the authenticated user.

    Raises:
        InvalidTokenException: Token is missing, malformed, or expired.
        UserNotFoundException: Token is valid but user no longer exists.
    """
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise InvalidTokenException()
    except JWTError:
        raise InvalidTokenException()

    user = await UserService.get_by_id(db, int(user_id))
    if user is None:
        raise UserNotFoundException()

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency: Ensures the authenticated user's account is active.

    Raises:
        ForbiddenException: If user account is deactivated.
    """
    if not current_user.is_active:
        raise ForbiddenException(detail="Your account has been deactivated")
    return current_user


async def require_teacher(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Dependency: Restricts endpoint access to Teacher role only.

    Raises:
        ForbiddenException: If user is not a teacher.
    """
    if current_user.role != UserRole.TEACHER:
        raise ForbiddenException(detail="Only teachers can access this resource")
    return current_user


async def require_student(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Dependency: Restricts endpoint access to Student role only.

    Raises:
        ForbiddenException: If user is not a student.
    """
    if current_user.role != UserRole.STUDENT:
        raise ForbiddenException(detail="Only students can access this resource")
    return current_user


# ─── Convenience Annotated Types ──────────────────────────────────────────────
CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentTeacher = Annotated[User, Depends(require_teacher)]
CurrentStudent = Annotated[User, Depends(require_student)]
