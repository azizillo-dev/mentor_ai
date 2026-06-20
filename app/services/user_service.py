"""
User service: CRUD operations for the User model.
All database interactions go through this layer.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserService:
    """
    Service class for user-related database operations.

    All methods are static/class methods since they only need
    the db session passed in — no instance state needed.
    """

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        """Fetch a user by their primary key ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        """Fetch a user by their email address (case-insensitive)."""
        result = await db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def email_exists(db: AsyncSession, email: str) -> bool:
        """Check if an email address is already registered."""
        user = await UserService.get_by_email(db, email)
        return user is not None

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        email: str,
        full_name: str,
        hashed_password: str,
        role: UserRole = UserRole.STUDENT,
    ) -> User:
        """
        Create and persist a new user.

        Args:
            db: Async database session.
            email: User's email (stored lowercase).
            full_name: User's display name.
            hashed_password: Bcrypt-hashed password (never plain-text).
            role: User role (teacher or student).

        Returns:
            The newly created User instance.
        """
        user = User(
            email=email.lower().strip(),
            full_name=full_name.strip(),
            hashed_password=hashed_password,
            role=role,
        )
        db.add(user)
        await db.flush()   # Get auto-generated ID before commit
        await db.refresh(user)
        return user

    @staticmethod
    async def update_active_status(
        db: AsyncSession,
        user: User,
        is_active: bool,
    ) -> User:
        """Activate or deactivate a user account."""
        user.is_active = is_active
        await db.flush()
        await db.refresh(user)
        return user
