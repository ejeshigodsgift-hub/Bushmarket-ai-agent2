# =========================================
# FILE: app/db/models/escrow_account.py
# =========================================

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Boolean,
    func,
    Index,
    UniqueConstraint
)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.db.base import Base


class EscrowAccount(Base):

    __tablename__ = "escrow_accounts"

    __table_args__ = (
        UniqueConstraint("cooperative_id", name="uq_escrow_cooperative"),
        Index("idx_escrow_status", "status"),
        Index("idx_escrow_cooperative", "cooperative_id"),
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
    # LINKED COOPERATIVE
    # =========================
    cooperative_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cooperatives.id", ondelete="CASCADE"),
        nullable=False
    )

    # =========================
    # FINANCIAL STATE
    # =========================
    total_deposited: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=0,
        nullable=False
    )

    total_reserved: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=0,
        nullable=False
    )

    available_balance: Mapped[Decimal] = mapped_column(
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

    type: Mapped[str] =    mapped_column(String(30), nullable=False)

    # =========================
    # STATUS
    # =========================
    status: Mapped[str] = mapped_column(
        String(30),
        default="active",  # active | frozen | released | closed
        nullable=False
    )

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

    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # =========================
    # RELATIONSHIP
    # =========================
    cooperative = relationship(
        "Cooperative",
        lazy="selectin"
    )

    transactions = relationship(
        "EscrowTransaction",
        back_populates="escrow_account",
        cascade="all, delete-orphan"
    )