# =========================================
# FILE: app/db/models/notification.py
# =========================================

import uuid

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    func,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class Notification(Base):

    __tablename__ = "notifications"

    __table_args__ = (
        Index("idx_notification_user", "user_id"),
        Index("idx_notification_status", "status"),
        Index("idx_notification_channel", "channel"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    channel: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    """
    email
    sms
    push
    """

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False
    )
    """
    pending
    sent
    delivered
    failed
    """

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    sent_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True)
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    user = relationship(
        "User",
        lazy="selectin"
    )