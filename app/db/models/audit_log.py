# =====================================
# FILE: app/db/models/audit_log.py
# =====================================

import uuid

from sqlalchemy import (
    String,
    JSON,
    DateTime,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base


class AuditLog(Base):

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    entity_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    event_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    ip_address: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    # =====================================
    # NEW FIELDS (ALIGNED WITH SERVICE)
    # =====================================

    session_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    device_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )