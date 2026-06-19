import uuid

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Boolean,
    func,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.db.base import Base


class PaymentIntent(Base):
    """
    Core payment initialization record
    """

    __tablename__ = "payment_intents"

    __table_args__ = (
        Index("idx_payment_intent_user", "user_id"),
        Index("idx_payment_intent_status", "status"),
        Index("idx_payment_intent_reference", "reference"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
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

    purpose: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    """
    order | cooperative_membership | wallet_topup | escrow_fund
    """

    reference: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False
    )
    """
    pending | processing | successful | failed | cancelled
    """

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    checkout_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("checkouts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    checkout = relationship(
        "Checkout",
        back_populates="payment_intents",
        lazy="joined"
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    transactions = relationship(
        "PaymentTransaction",
        back_populates="intent",
        lazy="selectin"
    )