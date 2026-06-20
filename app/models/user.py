"""
User model with Teacher and Student roles.
"""

import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.group import Group


class UserRole(str, enum.Enum):
    """
    User roles in the Men Mentor platform.

    TEACHER: Can create groups, assign homework, view submissions, see AI results.
    STUDENT: Can join groups, submit homework, view their own AI results.
    """

    TEACHER = "teacher"
    STUDENT = "student"


class User(BaseModel):
    """
    User model representing both teachers and students.

    Table: users
    """

    __tablename__ = "users"

    # ─── Identity ─────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # ─── Role & Status ────────────────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"),
        nullable=False,
        default=UserRole.STUDENT,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # ─── Relationships ────────────────────────────────────────────────────────
    groups: Mapped[List["Group"]] = relationship(
        "Group",
        back_populates="teacher",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # ─── Properties ───────────────────────────────────────────────────────────
    @property
    def is_teacher(self) -> bool:
        return self.role == UserRole.TEACHER

    @property
    def is_student(self) -> bool:
        return self.role == UserRole.STUDENT

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r}, role={self.role.value!r})>"
