# =========================================
# FILE: app/db/models/order.py
# =========================================

import uuid
from decimal import Decimal

from sqlalchemy import (
    String,
    ForeignKey,
    Numeric,
    DateTime,
    Boolean,
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


class Order(Base):

    __tablename__ = "orders"

    __table_args__ = (

        Index("idx_order_user_id", "user_id"),
        Index("idx_order_checkout_id", "checkout_id"),
        Index("idx_order_status", "status"),
        Index("idx_order_payment_status", "payment_status"),
        Index("idx_order_number", "order_number"),

        CheckConstraint("total_amount >= 0", name="ck_order_total"),
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
    # ORDER NUMBER
    # =========================================

    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    # =========================================
    # RELATIONS
    # =========================================

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    checkout_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("checkouts.id", ondelete="SET NULL"),
        nullable=True
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
    # ORDER STATE
    # =========================================

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending"
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    
    # =========================================
# AMOUNT BREAKDOWN (FIX FOR SERVICE MISMATCH)
# =========================================

    subtotal_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    market_fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    delivery_fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    is_delivered: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    is_cancelled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
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

    delivered_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    cancelled_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # =========================================
    # RELATIONSHIPS
    # =========================================

    checkout = relationship(
        "Checkout",
        lazy="joined"
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )