import uuid

from decimal import Decimal
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Numeric,
    func,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class PricingSnapshot(Base):

    __tablename__ = "pricing_snapshots"

    __table_args__ = (
        Index("idx_snapshot_cart", "cart_item_id"),
        Index("idx_snapshot_checkout", "checkout_item_id"),
        Index("idx_snapshot_order", "order_item_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    listing_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("market_product_listings.id"),
        nullable=False
    )

    cart_item_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True
    )

    checkout_item_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True
    )

    order_item_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    quantity: Mapped[int]

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    market_fee: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    platform_fee: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    agent_fee: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=0
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=0
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )