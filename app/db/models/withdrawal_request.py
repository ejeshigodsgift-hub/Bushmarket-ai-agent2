import uuid

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    func,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from decimal import Decimal

from app.db.base import Base


class WithdrawalRequest(Base):

    __tablename__ = "withdrawal_requests"

    __table_args__ = (
        Index("idx_withdrawal_wallet", "wallet_id"),
        Index("idx_withdrawal_status", "status"),
        Index("idx_withdrawal_reference", "reference"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    wallet_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False
    )

    beneficiary_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("beneficiaries.id", ondelete="RESTRICT"),
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    reference: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    gateway_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False
    )
    """
    pending
    fraud_review
    approved
    processing
    paid
    failed
    reversed
    cancelled
    """

    failure_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    processed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True)
    )

    wallet = relationship(
        "Wallet",
        lazy="joined"
    )

    beneficiary = relationship(
        "Beneficiary",
        lazy="joined"
    )