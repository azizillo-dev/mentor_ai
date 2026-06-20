"""
Homework SQLAlchemy model.
UUID primary key ishlatiladi.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class Homework(BaseModel):
    """
    Homework modeli — Teacher tomonidan Group uchun yaratiladi.

    Table: homeworks
    """

    __tablename__ = "homeworks"

    # ─── Primary Key (UUID) ───────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # ─── Foreign Key ──────────────────────────────────────────────────────────
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ─── Fields ───────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # ─── Relationships ────────────────────────────────────────────────────────
    group: Mapped["Group"] = relationship(  # type: ignore[name-defined]
        "Group",
        back_populates="homeworks",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Homework(id={self.id}, title={self.title!r}, group_id={self.group_id})>"
