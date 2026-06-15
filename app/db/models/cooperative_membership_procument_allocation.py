import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Numeric,
    Integer,
    DateTime,
    ForeignKey,
    func,
    Index,
    Boolean
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CooperativeMembershipProcurementAllocation(Base):
    """
    Final allocation per MEMBER inside a cooperative.

    This is the MOST IMPORTANT allocation layer:

    - Cooperative allocation → split across cooperatives
    - Membership allocation → split across members
    """

    __tablename__ = "cooperative_membership_procurement_allocations"

    __table_args__ = (
        Index("idx_member_alloc_procurement", "procurement_id"),
        Index("idx_member_alloc_membership", "membership_id"),
        Index("idx_member_alloc_user", "user_id"),
    )

    # =====================================
    # PRIMARY KEY
    # =====================================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =====================================
    # LINKS
    # =====================================
    procurement_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cooperative_procurements.id", ondelete="CASCADE"),
        nullable=False
    )

    cooperative_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cooperatives.id", ondelete="CASCADE"),
        nullable=False
    )

    membership_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cooperative_memberships.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # =====================================
    # ALLOCATION LOGIC
    # =====================================
    allocation_ratio: Mapped[float] = mapped_column(
        Numeric(10, 6),
        nullable=False
    )
    """
    Example:
    0.25 = 25% of cooperative allocation
    """

    allocated_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    allocated_value: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    allocated_savings: Mapped[float | None] = mapped_column(
        Numeric(18, 2),
        nullable=True
    )

    # =====================================
    # STATUS
    # =====================================
    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        nullable=False
    )
    """
    active
    adjusted
    delivered
    reconciled
    refunded
    """

    # =====================================
    # OPTIONAL FLAGS
    # =====================================
    is_partial_allocation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # =====================================
    # TIMESTAMPS
    # =====================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now()
    )

    # =====================================
    # RELATIONSHIPS
    # =====================================
    procurement = relationship(
        "CooperativeProcurement",
        lazy="selectin"
    )

    cooperative = relationship(
        "Cooperative",
        lazy="selectin"
    )

    membership = relationship(
        "CooperativeMembership",
        lazy="selectin"
    )

    user = relationship(
        "User",
        lazy="selectin"
    )