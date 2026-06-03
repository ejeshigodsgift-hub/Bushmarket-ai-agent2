# =========================================
# FILE: app/db/models/escrow_transaction.py
# =========================================

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    func,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EscrowTransaction(Base):

    __tablename__ = "escrow_transactions"

    __table_args__ = (
        Index("idx_escrow_tx_account", "escrow_account_id"),
        Index("idx_escrow_tx_type", "transaction_type"),
        Index("idx_escrow_tx_reference", "reference"),
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
    # ESCROW LINK
    # =========================
    escrow_account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("escrow_accounts.id", ondelete="CASCADE"),
        nullable=False
    )

    # =========================
    # TRANSACTION DETAILS
    # =========================
    transaction_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    # deposit | hold | release | refund | adjustment

    amount: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    reference: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="successful",
        nullable=False
    )

    metadata: Mapped[dict | None] = mapped_column(
        String,
        nullable=True
    )

    # =========================
    # TIMESTAMPS
    # =========================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # =========================
    # RELATIONSHIP
    # =========================
    escrow_account = relationship(
        "EscrowAccount",
        back_populates="transactions",
        lazy="selectin"
    )