# =========================================
# FILE: app/db/models/order_item.py
# =========================================

import uuid
from decimal import Decimal

from sqlalchemy import (
    String,
    ForeignKey,
    Integer,
    Numeric,
    DateTime,
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


class OrderItem(Base):

    __tablename__ = "order_items"

    __table_args__ = (

        Index("idx_order_item_order_id", "order_id"),
        Index("idx_order_item_listing_id", "listing_id"),
        Index("idx_order_item_product_id", "product_id"),

        CheckConstraint("quantity > 0", name="ck_order_item_quantity"),
        CheckConstraint("unit_price >= 0", name="ck_order_item_price"),
        CheckConstraint("market_fee >= 0", name="ck_order_item_fee"),
        CheckConstraint("total_price >= 0", name="ck_order_item_total"),
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
    # RELATIONS
    # =========================================

    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )

    listing_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("market_product_listings.id", ondelete="RESTRICT"),
        nullable=False
    )

    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False
    )

    market_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("market_locations.id", ondelete="RESTRICT"),
        nullable=False
    )

    measurement_unit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("measurement_units.id", ondelete="RESTRICT"),
        nullable=False
    )

    # =========================================
    # ORDER SNAPSHOT
    # =========================================

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    market_fee: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    total_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    # =========================================
    # DELIVERY
    # =========================================

    delivery_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending"
    )

    # =========================================
    # TIMESTAMPS
    # =========================================

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # =========================================
    # RELATIONSHIPS
    # =========================================

    order = relationship(
        "Order",
        back_populates="items",
        lazy="selectin"
    )

    listing = relationship(
        "MarketProductListing",
        lazy="joined"
    )

    product = relationship(
        "Product",
        lazy="joined"
    )

    market = relationship(
        "MarketLocation",
        lazy="joined"
    )

    measurement_unit = relationship(
        "MeasurementUnit",
        lazy="joined"
    )