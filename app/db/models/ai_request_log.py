import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    Text,
    Numeric,
    Integer,
    JSON,
    func,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base


class AIRequestLog(Base):
    __tablename__ = "ai_request_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        index=True,
        nullable=True
    )

    conversation_id: Mapped[str | None] = mapped_column(
        String(36),
        index=True,
        nullable=True
    )

    operation: Mapped[str] = mapped_column(
        String(100),
        index=True
    )

    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    prompt_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    completion_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    total_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    estimated_cost: Mapped[float] = mapped_column(
        Numeric(12, 6),
        default=0
    )

    latency_ms: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="success",
        index=True
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        Index("idx_ai_log_operation", "operation"),
        Index("idx_ai_log_status", "status"),
        Index("idx_ai_log_user", "user_id"),
        Index("idx_ai_log_conversation", "conversation_id"),
        Index("idx_ai_log_created", "created_at"),
    )