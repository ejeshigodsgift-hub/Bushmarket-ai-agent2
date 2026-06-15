import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import (
    String,
    Numeric,
    Integer,
    DateTime,
    ForeignKey,
    func,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CooperativeProcurementAllocation(Base):
    """
    Stores how a merged procurement is split
    across cooperatives based on contribution ratio.
    """

    __tablename__ = "cooperative_procurement_allocations"

    __table_args__ = (
        Index("idx_procurement_allocation_procurement", "procurement_id"),
        Index("idx_procurement_allocation_cooperative", "cooperative_id"),
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

    # =====================================
    # ALLOCATION METRICS
    # =====================================
    allocation_ratio: Mapped[Decimal] = mapped_column(
        Numeric(8, 6),
        nullable=False
    )
    """
    Example:
    0.40 = 40%
    """

    allocated_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    allocated_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    # Optional: derived savings per cooperative
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
    """

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