"""
Group Member SQLAlchemy model.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.user import User


class GroupMember(BaseModel):
    """
    Group va Student orasidagi Many-to-Many ulanishni bildiradi.
    Lekin biz qo'shimcha ma'lumotlar saqlash uchun explicit model ishlatamiz.
    
    Table: group_members
    """
    __tablename__ = "group_members"

    # ─── Primary Key (UUID) ───────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # ─── Foreign Keys ─────────────────────────────────────────────────────────
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ─── Fields ───────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Bitta o'quvchi bitta guruhga faqat 1 marta a'zo bo'la oladi
    __table_args__ = (
        UniqueConstraint("group_id", "student_id", name="uq_group_student"),
    )

    # ─── Relationships ────────────────────────────────────────────────────────
    group: Mapped["Group"] = relationship(
        "Group",
        back_populates="members",
        lazy="select",
    )
    student: Mapped["User"] = relationship(
        "User",
        back_populates="memberships",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<GroupMember(id={self.id}, group_id={self.group_id}, student_id={self.student_id})>"
