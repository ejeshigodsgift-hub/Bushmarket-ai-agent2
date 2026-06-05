import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Boolean,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    # =========================
    # PRIMARY ID
    # =========================

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # USER RELATION
    # =========================

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # =========================
    # COOPERATIVE RELATION
    # =========================

    cooperative_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True
    )

    membership_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    


    # =========================
    # TOKENS
    # =========================

    session_token: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    refresh_token: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    # =========================
    # DEVICE + SECURITY
    # =========================

    device_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True
    )

    device_name: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    user_agent: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    ip_address: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    # =========================
    # SECURITY FIX (MISSING FIELD ADDED)
    # =========================

    fingerprint: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True
    )

    # =========================
    # SESSION STATUS
    # =========================

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # =========================
    # SESSION LIFECYCLE
    # =========================

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    refresh_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # =========================
    # TIMESTAMPS
    # =========================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # =========================
    # RELATIONSHIP
    # =========================

    user = relationship(
        "User",
        backref="sessions"
    )