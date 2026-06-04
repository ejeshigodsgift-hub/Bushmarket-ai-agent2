# =========================================
# FILE: app/db/models/cooperative_wallet.py
# =========================================

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Boolean,
    func,
    Index,
    CheckConstraint
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CooperativeWallet(Base):
    """
    Cooperative pooled wallet (group buying financial layer)
    """

    __tablename__ = "cooperative_wallets"

    __table_args__ = (
        Index("idx_coop_wallet_cooperative", "cooperative_id"),
        Index("idx_coop_wallet_status", "status"),

        CheckConstraint("balance >= 0", name="ck_coop_wallet_balance_positive"),
        CheckConstraint("frozen_balance >= 0", name="ck_coop_wallet_frozen_positive"),
    )

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # LINK TO COOPERATIVE
    # =========================
    cooperative_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cooperatives.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    # =========================
    # BALANCES
    # =========================

    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False
    )

    frozen_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False
    )

    available_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False
    )

    ledger_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
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

    # =========================
    # STATUS CONTROL
    # =========================
    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        nullable=False
    )
    # active | frozen | suspended | closed

    is_frozen: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # =========================
    # TIMESTAMPS
    # =========================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # =========================
    # RELATIONSHIPS
    # =========================
    cooperative = relationship(
        "Cooperative",
        lazy="selectin"
    )

    transactions = relationship(
        "CooperativeWalletTransaction",
        back_populates="wallet",
        cascade="all, delete-orphan",
        lazy="selectin"
    )