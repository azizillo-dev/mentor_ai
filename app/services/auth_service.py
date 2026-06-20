"""
Authentication service: registration, login, and token generation logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyExistsException,
    InvalidCredentialsException,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.user_service import UserService


class AuthService:
    """
    Service responsible for authentication flows.
    Orchestrates UserService and security utilities.
    """

    @staticmethod
    def _build_token_response(user: User) -> TokenResponse:
        """Create a TokenResponse for the given user."""
        access_token = create_access_token(subject=user.id)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    async def register(
        db: AsyncSession,
        payload: RegisterRequest,
    ) -> tuple[User, TokenResponse]:
        """
        Register a new user account.

        Steps:
          1. Check email uniqueness.
          2. Hash the password.
          3. Persist the user.
          4. Generate access token.

        Args:
            db: Async database session.
            payload: Validated registration data.

        Returns:
            Tuple of (created User, TokenResponse).

        Raises:
            EmailAlreadyExistsException: If email is taken.
        """
        # 1. Check uniqueness
        if await UserService.email_exists(db, payload.email):
            raise EmailAlreadyExistsException()

        # 2. Hash password
        hashed = hash_password(payload.password)

        # 3. Create user
        user = await UserService.create(
            db,
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hashed,
            role=payload.role,
        )

        # 4. Generate token
        token = AuthService._build_token_response(user)

        return user, token

    @staticmethod
    async def login(
        db: AsyncSession,
        payload: LoginRequest,
    ) -> tuple[User, TokenResponse]:
        """
        Authenticate an existing user.

        Steps:
          1. Look up user by email.
          2. Verify password against bcrypt hash.
          3. Ensure account is active.
          4. Generate access token.

        Args:
            db: Async database session.
            payload: Login credentials.

        Returns:
            Tuple of (authenticated User, TokenResponse).

        Raises:
            InvalidCredentialsException: If credentials are wrong or account inactive.
        """
        # 1. Fetch user
        user = await UserService.get_by_email(db, payload.email)

        # 2. Verify password (use same error to prevent user enumeration)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise InvalidCredentialsException()

        # 3. Check active status
        if not user.is_active:
            raise InvalidCredentialsException()

        # 4. Generate token
        token = AuthService._build_token_response(user)

        return user, token
