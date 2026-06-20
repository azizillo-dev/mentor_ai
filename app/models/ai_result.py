"""
AIResult SQLAlchemy model.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class AIResult(BaseModel):
    """
    AIResult modeli — Gemini API orqali tekshirilgan submission natijasi.

    Table: ai_results
    """

    __tablename__ = "ai_results"

    # ─── Primary Key (UUID) ───────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # ─── Foreign Key ──────────────────────────────────────────────────────────
    # 1 to 1 relation with Submission
    submission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # ─── AI Response Fields ───────────────────────────────────────────────────
    score_percent: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[list] = mapped_column(JSON, nullable=False)
    weaknesses: Mapped[list] = mapped_column(JSON, nullable=False)
    suggestions: Mapped[list] = mapped_column(JSON, nullable=False)
    raw_response: Mapped[dict] = mapped_column(JSON, nullable=False)

    # ─── Relationships ────────────────────────────────────────────────────────
    submission: Mapped["Submission"] = relationship("Submission", lazy="select")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<AIResult(id={self.id}, submission_id={self.submission_id}, score={self.score_percent}%)>"
