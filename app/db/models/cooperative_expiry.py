import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Text,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CooperativeExpiry(Base):
    """
    Cooperative Expiry Lifecycle Event Log

    This table is an EVENT/AUDIT log, not state storage.
    It tracks lifecycle transitions like:
    - expiry window opened
    - cooperative extended
    - cooperative expired
    """

    __tablename__ = "cooperative_expiry_events"

    __table_args__ = (
        Index("idx_expiry_cooperative_id", "cooperative_id"),
        Index("idx_expiry_event_type", "event_type"),
        Index("idx_expiry_created_at", "created_at"),
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
    # COOPERATIVE REFERENCE
    # =========================
    cooperative_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cooperatives.id", ondelete="CASCADE"),
        nullable=False
    )

    # =========================
    # EVENT TYPE
    # =========================
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    """
    expiry_window_open
    expired
    extended
    """

    # =========================
    # OPTIONAL CONTEXT
    # =========================
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        String,
        nullable=True
    )

    # =========================
    # TIMESTAMP
    # =========================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )