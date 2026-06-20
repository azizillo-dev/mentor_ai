"""
Group SQLAlchemy model.
UUID primary key ishlatiladi — global unique, predictable emas.
"""

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.homework import Homework


class Group(BaseModel):
    """
    Group modeli — Teacher tomonidan yaratiladi.

    Teacher -> Group munosabati: bir teacher ko'p groupga ega bo'lishi mumkin.

    Table: groups
    """

    __tablename__ = "groups"

    # ─── Primary Key (UUID) ───────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # ─── Foreign Key ──────────────────────────────────────────────────────────
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ─── Fields ───────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    subject: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ─── Relationships ────────────────────────────────────────────────────────
    teacher: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="groups",
        lazy="select",
    )
    homeworks: Mapped[List["Homework"]] = relationship(
        "Homework",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Group(id={self.id}, name={self.name!r}, teacher_id={self.teacher_id})>"
