import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import JSON

from sqlalchemy import (
    String,
    DateTime,
    Numeric,
    Boolean,
    ForeignKey,
    Text,
    func,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FinancialReconciliation(Base):
    """
    FINANCIAL RECONCILIATION MODEL (BushMarket Core Integrity Layer)

    PURPOSE:
    - Ensures FinancialCore == Escrow == Wallet == Ledger alignment
    - Detects mismatches in cooperative funds
    - Supports audit + admin investigation
    - Tracks reconciliation jobs per cooperative lifecycle
    """

    __tablename__ = "financial_reconciliations"

    __table_args__ = (
        Index("idx_recon_cooperative", "cooperative_id"),
        Index("idx_recon_status", "status"),
        Index("idx_recon_type", "reconciliation_type"),
        Index("idx_recon_reference", "reference"),
    )

    # =========================================
    # PRIMARY KEY
    # =========================================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================================
    # LINK TO COOPERATIVE (OPTIONAL GLOBAL RECONCILIATION SUPPORT)
    # =========================================
    cooperative_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("cooperatives.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # =========================================
    # RECONCILIATION TYPE
    # =========================================
    reconciliation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    """
    cooperative_wallet
    escrow_vs_ledger
    wallet_vs_ledger
    full_system_audit
    partial_procurement_check
    refund_reconciliation
    """

    # =========================================
    # FINANCIAL VALUES SNAPSHOT
    # =========================================
    expected_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    actual_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    difference: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="NGN",
        nullable=False
    )

    # =========================================
    # STATUS
    # =========================================
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False
    )
    """
    pending
    matched
    mismatch
    resolved
    escalated
    """

    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # =========================================
    # REFERENCE TRACKING
    # =========================================
    reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    ledger_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    escrow_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    wallet_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    financial_core_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    # =========================================
    # ANALYSIS DATA (DEBUG + AUDIT SUPPORT)
    # =========================================
    mismatch_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    metadata: Mapped[dict | None] =  mapped_column(JSON, nullable=True)
    # =========================================
    # TIMESTAMPS
    # =========================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    escalated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # =========================================
    # RELATIONSHIPS
    # =========================================
    cooperative = relationship(
        "Cooperative",
        lazy="selectin"
    )