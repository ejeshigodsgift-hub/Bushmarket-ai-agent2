# =========================================
# FILE: app/db/models/checkout.py
# =========================================

import uuid
from decimal import Decimal

from sqlalchemy import (
    String,
    ForeignKey,
    Numeric,
    DateTime,
    Boolean,
    Integer,
    func,
    Index,
    CheckConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class Checkout(Base):

    __tablename__ = "checkouts"

    __table_args__ = (

        Index("idx_checkout_user_id", "user_id"),
        Index("idx_checkout_cart_id", "cart_id"),
        Index("idx_checkout_status", "status"),
        Index("idx_checkout_payment_status", "payment_status"),

        CheckConstraint("subtotal >= 0", name="ck_checkout_subtotal"),
        CheckConstraint("market_fee_total >= 0", name="ck_checkout_market_fee"),
        CheckConstraint("delivery_fee >= 0", name="ck_checkout_delivery_fee"),
        CheckConstraint("total >= 0", name="ck_checkout_total"),
    )

    # =========================================
    # PRIMARY KEY
    # =========================================

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================================
    # RELATION KEYS
    # =========================================

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    cart_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("carts.id", ondelete="SET NULL"),
        nullable=True
    )

    order_id = mapped_column(
        String(36),
        ForeignKey(
            "orders.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # =========================================
    # FINANCIALS
    # =========================================

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    market_fee_total: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    # =========================================
    # PAYMENT
    # =========================================

    payment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending"
    )

    payment_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    # =========================================
    # CHECKOUT STATUS
    # =========================================

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending"
    )

    expires_in_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=15
    )

    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    # =========================================
    # TIMESTAMPS
    # =========================================

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

    completed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # =========================================
    # RELATIONSHIPS
    # =========================================

    cart = relationship(
        "Cart",
        lazy="joined"
    )

    items = relationship(
        "CheckoutItem",
        back_populates="checkout",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


    payment_intents = relationship(
        "PaymentIntent",
        back_populates="checkout",
        lazy="selectin"
    )