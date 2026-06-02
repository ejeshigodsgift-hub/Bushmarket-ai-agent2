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

from app.db.base import Base


class PaymentTransaction(Base):
    """
    Gateway-level payment lifecycle tracking
    """

    __tablename__ = "payment_transactions"

    __table_args__ = (
        Index("idx_payment_tx_intent", "intent_id"),
        Index("idx_payment_tx_gateway_ref", "gateway_reference"),
        Index("idx_payment_tx_status", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    intent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("payment_intents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    gateway: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    """
    paystack | flutterwave | stripe | internal
    """

    gateway_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )

    amount: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False
    )
    """
    pending | success | failed | reversed
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

    intent = relationship(
        "PaymentIntent",
        back_populates="transactions",
        lazy="selectin"
    )