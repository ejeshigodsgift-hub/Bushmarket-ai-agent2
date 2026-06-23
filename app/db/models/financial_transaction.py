import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import JSON

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Text,
    func,
    Index,
    UniqueConstraint
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FinancialTransaction(Base):
    """
    Immutable financial source-of-truth record.

    Every financial movement across:
    - Wallets
    - Escrow
    - Ledger
    - Payments
    - Refunds
    - Settlements
    """

    __tablename__ = "financial_transactions"

    __table_args__ = (
        UniqueConstraint(
            "reference",
            name="uq_financial_transactions_reference"
        ),

        # =========================
        # CORE INDEXES
        # =========================
        Index("idx_financial_tx_reference", "reference"),
        Index("idx_financial_tx_type", "transaction_type"),
        Index("idx_financial_tx_status", "status"),
        Index("idx_financial_tx_wallet", "wallet_id"),
        Index("idx_financial_tx_escrow", "escrow_account_id"),

        # =========================
        # 🟥 CORE BUSINESS LINKS
        # =========================
        Index("idx_tx_cooperative", "cooperative_id"),
        Index("idx_tx_procurement", "procurement_id"),
        Index("idx_tx_membership", "membership_id"),
        Index("idx_tx_shopper", "shopper_id"),
        Index("idx_tx_release_auth", "cooperative_release_authorization_id"),

        # =========================
        # 🟧 TRACEABILITY
        # =========================
        Index("idx_tx_entity", "entity_type", "entity_id"),
        Index("idx_tx_escrow_batch", "escrow_batch_id"),
        Index("idx_tx_ledger_batch", "ledger_batch_reference"),

        # =========================
        # 🟨 SAFETY / CONTROL
        # =========================
        Index("idx_tx_idempotency", "idempotency_key"),
    )

    # =====================================================
    # PRIMARY KEY
    # =====================================================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =====================================================
    # CORE IDENTITY
    # =====================================================
    reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )

    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="NGN",
        nullable=False
    )

    # =====================================================
    # 🟥 CORE BUSINESS LINKS (BUSHMARKET DOMAIN)
    # =====================================================
    shopper_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    cooperative_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("cooperatives.id"),
        nullable=True,
        index=True
    )

    procurement_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("cooperative_procurements.id"),
        nullable=True,
        index=True
    )

    membership_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("cooperative_memberships.id"),
        nullable=True,
        index=True
    )

    cooperative_release_authorization_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True
    )

    # =====================================================
    # 🟧 SYSTEM TRACEABILITY
    # =====================================================
    entity_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    entity_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True
    )

    escrow_batch_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True
    )

    ledger_batch_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )

    # =====================================================
    # LEDGER LINKS
    # =====================================================
    wallet_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("wallets.id"),
        nullable=True
    )

    escrow_account_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("escrow_accounts.id"),
        nullable=True
    )


    payment_intent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "payment_intents.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    payment_transaction_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "payment_transactions.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )


    debit_ledger_account_id: Mapped[str | None] = mapped_column(String(36))
    credit_ledger_account_id: Mapped[str | None] = mapped_column(String(36))

    # =====================================================
    # 🟨 SAFETY / FINANCIAL CONTROL
    # =====================================================
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True
    )

    authorization_status_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # =====================================================
    # STATUS
    # =====================================================
    status: Mapped[str] = mapped_column(
        String(30),
        default="completed",
        nullable=False,
        index=True
    )

    # =====================================================
    # AUDIT
    # =====================================================
    created_by: Mapped[str | None] = mapped_column(String(36))
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # =====================================================
    # TIMESTAMP
    # =====================================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================
    wallet = relationship("Wallet", lazy="selectin")
    escrow_account = relationship("EscrowAccount", lazy="selectin")
    payment_intent = relationship("PaymentIntent", lazy="selectin")
    payment_transaction = relationship("PaymentTransaction", lazy="selectin")