import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Numeric,
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


class CooperativeRefund(Base):
    """
    Cooperative Refund Record

    Used for:

    - cooperative expiration
    - failed procurement
    - cancelled cooperative
    - dispute resolution
    - member refunds

    FinancialCore executes money movement.
    This model records cooperative refund history.
    """

    __tablename__ = "cooperative_refunds"

    __table_args__ = (
        Index(
            "idx_coop_refund_cooperative",
            "cooperative_id"
        ),
        Index(
            "idx_coop_refund_user",
            "user_id"
        ),
        Index(
            "idx_coop_refund_membership",
            "membership_id"
        ),
        Index(
            "idx_coop_refund_status",
            "status"
        ),
        Index(
            "idx_coop_refund_reference",
            "refund_reference"
        ),
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
    # RELATIONSHIPS
    # =====================================
    cooperative_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "cooperatives.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    membership_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "cooperative_memberships.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    contribution_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "cooperative_contributions.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # =====================================
    # REFUND VALUE
    # =====================================
    refund_amount: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="NGN",
        nullable=False
    )

    # =====================================
    # REFERENCES
    # =====================================
    refund_reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    ledger_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    escrow_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    # =====================================
    # STATUS
    # =====================================
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False
    )
    """
    pending
    processing
    completed
    failed
    reversed
    """

    # =====================================
    # REFUND REASON
    # =====================================
    refund_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    """
    cooperative_expired
    procurement_failed
    dispute_resolution
    admin_override
    cancelled
    """

    admin_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # PROCUREMENT LINK
    procurement_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "cooperative_procurements.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # FUTURE WALLET SUPPORT
    cooperative_wallet_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True
    )

    # REFUND CLASSIFICATION
    refund_type: Mapped[str] = mapped_column(
        String(30),
        default="full",
        nullable=False
    )
    """
    full
    partial
    procurement_adjustment
    merge_adjustment
    admin_adjustment
"""

    # PARTIAL PROCUREMENT FLAG
    is_partial_procurement_related:     
    Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # MERGE / FUNDING ROUND SUPPORT
    funding_round: Mapped[int] = mapped_column(
        default=1,
        nullable=False
    )

    # DIRECT FINANCIAL CORE LINK
    financial_transaction_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )
    

    # =====================================
    # TIMESTAMPS
    # =====================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # =====================================
    # RELATIONSHIPS
    # =====================================
    cooperative = relationship(
        "Cooperative",
        lazy="selectin"
    )

    membership = relationship(
        "CooperativeMembership",
        lazy="selectin"
    )

    contribution = relationship(
        "CooperativeContribution",
        lazy="selectin"
    )

    user = relationship(
        "User",
        lazy="selectin"
    )

    procurement = relationship(
        "CooperativeProcurement",
        lazy="selectin"
    )
 

