import uuid

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    func,
    Index,
    UniqueConstraint
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WalletTransaction(Base):
    """
    Immutable wallet movement log
    """

    __tablename__ = "wallet_transactions"

    __table_args__ = (
        Index("idx_wallet_tx_wallet", "wallet_id"),
        Index("idx_wallet_tx_reference", "reference"),
        Index("idx_wallet_tx_type", "tx_type"),

        # 🔒 CRITICAL FIX: prevents duplicate credits/debits per reference
        UniqueConstraint(
            "reference",
            "tx_type",
            name="uq_wallet_tx_reference_type"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    wallet_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    tx_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    """
    credit | debit | escrow_hold | escrow_release | refund
    """

    amount: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="success",
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    wallet = relationship(
        "Wallet",
        back_populates="transactions",
        lazy="selectin"
    )