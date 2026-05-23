import uuid

from sqlalchemy import (
    String,
    DateTime,
    func,
    JSON
)

from sqlalchemy.orm import Mapped, mapped_column

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
        index=True
    )

    action: Mapped[str] = mapped_column(
        String(100)
    )

    entity_type: Mapped[str] = mapped_column(
        String(100)
    )

    entity_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    event_data: Mapped[dict] = mapped_column(
        JSON
    )

    ip_address: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )