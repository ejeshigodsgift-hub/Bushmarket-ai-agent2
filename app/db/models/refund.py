# =========================================
# FILE: app/db/models/refund.py
# =========================================

import uuid

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
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


class Refund(Base):

    __tablename__ = "refunds"

    __table_args__ = (
        Index("idx_refund_order", "order_id"),
        Index("idx_refund_payment_tx", "payment_transaction_id"),
        Index("idx_refund_status", "status"),
        Index("idx_refund_reference", "refund_reference"),

        CheckConstraint(
            "amount >= 0",
            name="ck_refund_amount_positive"
        ),
    )

    # =====================================
    # PRIMARY KEY
    # =====================================

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =====================================
    # LINKS
    # =====================================

    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "orders.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    payment_transaction_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "payment_transactions.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================
    # REFUND DETAILS
    # =====================================

    amount: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    refund_reference: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    gateway_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    # =====================================
    # STATUS
    # =====================================

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending"
    )

    """
    pending
    processing
    successful
    failed
    cancelled
    """

    # =====================================
    # AUDIT
    # =====================================

    processed_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # =====================================
    # TIMESTAMPS
    # =====================================

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    processed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # =====================================
    # RELATIONSHIPS
    # =====================================

    order = relationship(
        "Order",
        lazy="selectin"
    )

    payment_transaction = relationship(
        "PaymentTransaction",
        lazy="selectin"
    )