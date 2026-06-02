import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Boolean,
    func,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CooperativeMembership(Base):
    """
    Membership System for Cooperative Participation
    """

    __tablename__ = "cooperative_memberships"

    __table_args__ = (
        Index("idx_membership_user", "user_id"),
        Index("idx_membership_cooperative", "cooperative_id"),
        Index("idx_membership_status", "status"),
    )

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # RELATIONS
    # =========================
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

    # =========================
    # PAYMENT / CONTRIBUTION
    # =========================
    contribution_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # =========================
    # STATUS
    # =========================
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",  # pending → active → failed → refunded
        index=True
    )

    # =========================
    # PAYMENT REFERENCE (financial_core)
    # =========================
    payment_reference: Mapped[str | None] = mapped_column(String, nullable=True)

    # =========================
    # TIMESTAMPS
    # =========================
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # =========================
    # RELATIONSHIP
    # =========================
    cooperative = relationship(
        "Cooperative",
        back_populates="memberships"
    )

    user = relationship(
        "User",
        lazy="selectin"
    )