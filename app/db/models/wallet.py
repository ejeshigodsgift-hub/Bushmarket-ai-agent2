import uuid

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    func,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.db.base import Base


class Wallet(Base):
    """
    Unified Wallet (User + Cooperative compatible)
    """

    __tablename__ = "wallets"

    __table_args__ = (
        Index("idx_wallet_user", "user_id"),
        Index("idx_wallet_coop", "cooperative_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    cooperative_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("cooperatives.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=0,
        nullable=False
    )

    escrow_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=0,
        nullable=False
    )
    
    ledger_balance: Mapped[Decimal] = mapped_column(
        Numeric(18,2),
        default=0,
        nullable=False
    )
    
    

    currency: Mapped[str] = mapped_column(
        String(10),
        default="NGN",
        nullable=False
    )

    version: Mapped[int] = mapped_column(
        default=1,
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    transactions = relationship(
        "WalletTransaction",
        back_populates="wallet",
        lazy="selectin"
    )