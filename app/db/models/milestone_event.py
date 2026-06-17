# FILE: app/db/models/milestone_event.py

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MilestoneEvent(Base):
    """
    Tracks milestone notifications to prevent duplicate triggers
    """

    __tablename__ = "milestone_events"

    __table_args__ = (
        UniqueConstraint(
            "cooperative_id",
            "milestone",
            name="uq_coop_milestone_once"
        ),
        Index("idx_milestone_coop", "cooperative_id"),
    )

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # RELATION
    # =========================
    cooperative_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cooperatives.id", ondelete="CASCADE"),
        nullable=False
    )

    # =========================
    # MILESTONE TYPE
    # =========================
    milestone: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    # examples: "25%", "50%", "75%", "100%"

    # =========================
    # STATUS
    # =========================
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # optional audit/debug
    metadata: Mapped[str | None] = mapped_column(String(255))