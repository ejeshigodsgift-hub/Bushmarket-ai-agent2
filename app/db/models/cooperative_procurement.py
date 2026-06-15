import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Numeric,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    func,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class CooperativeProcurement(Base):
    """
    Procurement Record

    Supports:

    - Full procurement
    - Partial procurement
    - Procurement retries
    - Procurement tracking
    - Delivery tracking
    """

    __tablename__ = "cooperative_procurements"

    __table_args__ = (
        Index(
            "idx_procurement_cooperative",
            "cooperative_id"
        ),
        Index(
            "idx_procurement_status",
            "status"
        ),
        Index(
            "idx_procurement_type",
            "procurement_type"
        ),
    )

    # ====================================
    # PRIMARY KEY
    # ====================================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # ====================================
    # COOPERATIVE
    # ====================================
    cooperative_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "cooperatives.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    parent_cooperative_id: Mapped[str |    None] = mapped_column(
        String(36),
        ForeignKey("cooperatives.id"),
        nullable=True
    )

    # ====================================
    # PROCUREMENT TYPE
    # ====================================
    procurement_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    """
    full
    partial
    merged
    """

    

    #
 ====================================
    # FINANCIALS
    # ====================================
    procurement_value: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    procurement_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    estimated_retail_value: Mapped[float] = mapped_column(
        Numeric(18, 2),
        default=0
    )

    cooperative_buying_value: Mapped[float] = mapped_column(
        Numeric(18, 2),
        default=0
    )

    estimated_savings: Mapped[float] = mapped_column(
        Numeric(18, 2),
        default=0
    )

    savings_percentage: Mapped[float] = mapped_column(
        Numeric(8, 2),
        default=0
    )

    # ====================================
    # PROCUREMENT STATUS
    # ====================================
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending"
    )
    """
    pending
    approved
    purchasing
    purchased
    delivered
    completed
    failed
    refunded
    """

    # ====================================
    # ESCROW
    # ====================================
    escrow_released: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    escrow_release_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    # ====================================
    # FAILURE
    # ====================================
    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ====================================
    # TIMESTAMPS
    # ====================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    purchasing_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # ====================================
    # RELATIONSHIPS
    # ====================================
    cooperative = relationship(
        "Cooperative",
        lazy="selectin"
    )