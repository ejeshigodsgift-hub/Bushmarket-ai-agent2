# =========================================
# FILE: app/db/models/event_log.py
# =========================================

import uuid

from sqlalchemy import (
    String,
    DateTime,
    JSON,
    Text,
    Index,
    func
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base


class EventLog(Base):

    __tablename__ = "event_logs"

    # =========================================
    # PRIMARY KEY
    # =========================================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # =========================================
    # EVENT METADATA
    # =========================================
    event_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True
    )

    event_category: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True
    )

    topic: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True
    )

    source_service: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )

    # =========================================
    # ENTITY TRACKING
    # =========================================
    entity_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    entity_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True
    )

    # =========================================
    # USER TRACKING
    # =========================================
    user_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # =========================================
    # EVENT PAYLOAD
    # =========================================
    payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # =========================================
    # STATUS
    # =========================================
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="processed",
        index=True
    )

    # =========================================
    # TIMESTAMPS
    # =========================================
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # =========================================
    # INDEXES
    # =========================================
    __table_args__ = (
        Index(
            "idx_event_logs_entity_lookup",
            "entity_type",
            "entity_id"
        ),
        Index(
            "idx_event_logs_user_lookup",
            "user_id",
            "created_at"
        ),
    )