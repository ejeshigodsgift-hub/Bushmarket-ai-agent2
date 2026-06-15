import uuid
from datetime import datetime
from sqlalchemy import Boolean

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


class CooperativeContribution(Base):
    """
    Cooperative Contribution Audit Record

    Tracks every contribution made into a cooperative.

    FinancialCore remains source of truth.

    This model exists for:

    - dashboard analytics
    - cooperative reporting
    - member contribution history
    - reconciliation
    - refund calculations
    """

    __tablename__ = "cooperative_contributions"

    __table_args__ = (
        Index(
            "idx_coop_contribution_cooperative",
            "cooperative_id"
        ),
        Index(
            "idx_coop_contribution_user",
            "user_id"
        ),
        Index(
            "idx_coop_contribution_membership",
            "membership_id"
        ),
        Index(
            "idx_coop_contribution_reference",
            "payment_reference"
        ),
        Index(
            "idx_coop_contribution_status",
            "status"
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
            ondelete="CASCADE"
        ),
        nullable=False
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================
    # FINANCIALS
    # =====================================
    amount: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="NGN",
        nullable=False
    )

    # =====================================
    # FINANCIAL CORE REFERENCES
    # =====================================
    payment_reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    payment_intent_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
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
        default="completed",
        nullable=False
    )
    """
    pending
    completed
    reversed
    refunded
    failed
    """

    # =====================================
    # NOTES
    # =====================================
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # PROCUREMENT LINK
    procurement_id: Mapped[str | None] =   
mapped_column(
        String(36),
        ForeignKey(
            "cooperative_procurements.id",
        ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # FUTURE WALLET SUPPORT
    cooperative_wallet_id: Mapped[str |    
    None] = mapped_column(
        String(36),
        nullable=True,
        index=True
    )

# COOPERATIVE MERGE / MULTI-ROUND SUPPORT
    funding_round: Mapped[int] = mapped_column(
        default=1,
        nullable=False
    )

    # PARTIAL PROCUREMENT FLAG
    is_partial_procurement_related:   Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # DIRECT FINANCIAL CORE LINK
    financial_transaction_id: Mapped[str    
| None] = mapped_column(
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

    user = relationship(
        "User",
        lazy="selectin"
    )

    procurement = relationship(
        "CooperativeProcurement",
        lazy="selectin"
    )