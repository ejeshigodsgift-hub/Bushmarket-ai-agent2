import uuid
from datetime import datetime

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

    MUST generate one FinancialTransaction record.
    """

    __tablename__ = "financial_transactions"

    __table_args__ = (
        UniqueConstraint(
            "reference",
            name="uq_financial_transactions_reference"
        ),

        Index(
            "idx_financial_tx_reference",
            "reference"
        ),

        Index(
            "idx_financial_tx_type",
            "transaction_type"
        ),

        Index(
            "idx_financial_tx_status",
            "status"
        ),

        Index(
            "idx_financial_tx_wallet",
            "wallet_id"
        ),

        Index(
            "idx_financial_tx_escrow",
            "escrow_account_id"
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
    # REFERENCE
    # =====================================

    reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )

    # =====================================
    # TRANSACTION TYPE
    # =====================================

    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    """
    wallet_credit
    wallet_debit
    wallet_transfer
    escrow_deposit
    escrow_hold
    escrow_release
    refund
    settlement
    commission
    adjustment
    """

    # =====================================
    # FINANCIAL VALUE
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
    # WALLET
    # =====================================

    wallet_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "wallets.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # =====================================
    # ESCROW
    # =====================================

    escrow_account_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "escrow_accounts.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # =====================================
    # PAYMENT LINKS
    # =====================================

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

    # =====================================
    # LEDGER LINKS
    # =====================================

    debit_ledger_account_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "ledger_accounts.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    credit_ledger_account_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "ledger_accounts.id",
            ondelete="SET NULL"
        ),
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
    failed
    reversed
    """

    # =====================================
    # AUDIT
    # =====================================

    created_by: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True
    )

    metadata: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # =====================================
    # TIMESTAMP
    # =====================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # =====================================
    # RELATIONSHIPS
    # =====================================

    wallet = relationship(
        "Wallet",
        lazy="selectin"
    )

    escrow_account = relationship(
        "EscrowAccount",
        lazy="selectin"
    )

    payment_intent = relationship(
        "PaymentIntent",
        lazy="selectin"
    )

    payment_transaction = relationship(
        "PaymentTransaction",
        lazy="selectin"
    )