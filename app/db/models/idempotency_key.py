import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    __table_args__ = (
        Index("idx_idem_key", "key"),
        Index("idx_idem_reference", "reference"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    reference: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )