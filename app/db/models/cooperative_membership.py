import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Numeric,
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


class CooperativeMembership(Base):
    """
    Cooperative Membership

    Lifecycle:

    pending
        ↓
    active
        ↓
    refunded

    pending
        ↓
    failed
    """

    __tablename__ = "cooperative_memberships"

    __table_args__ = (
        Index("idx_membership_user", "user_id"),
        Index("idx_membership_cooperative", "cooperative_id"),
        Index("idx_membership_status", "status"),
        Index("idx_membership_payment_reference", "payment_reference"),
    )

    # ====================================================
    # PRIMARY KEY
    # ====================================================
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # ====================================================
    # RELATIONSHIPS
    # ====================================================
    cooperative_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("cooperatives.id"),
        nullable=False,
        index=True
    )

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # ====================================================
    # CONTRIBUTION
    # ====================================================
    contribution_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    # ====================================================
    # MEMBERSHIP STATUS
    # pending -> active -> refunded
    # pending -> failed
    # ====================================================
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True
    )

    # ====================================================
    # FINANCIAL CORE REFERENCE
    # ====================================================
    payment_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    # ====================================================
    # FAILURE TRACKING
    # ====================================================
    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ====================================================
    # LIFECYCLE TIMESTAMPS
    # ====================================================
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

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # ====================================================
    # RELATIONSHIPS
    # ====================================================
    cooperative = relationship(
        "Cooperative",
        back_populates="memberships"
    )

    user = relationship(
        "User",
        lazy="selectin"
    )