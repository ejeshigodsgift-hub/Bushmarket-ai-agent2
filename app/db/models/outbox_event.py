import uuid

from sqlalchemy import (
    String,
    Boolean,
    Integer,
    JSON,
    DateTime,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base


class OutboxEvent(Base):

    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    topic: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )