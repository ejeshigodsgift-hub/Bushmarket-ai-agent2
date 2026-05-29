# =========================================
# FILE: app/db/models/cart_item.py
# =========================================

import uuid
from decimal import Decimal

from sqlalchemy import (
    String,
    ForeignKey,
    Integer,
    Numeric,
    DateTime,
    Boolean,
    UniqueConstraint,
    Index,
    CheckConstraint,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class CartItem(Base):

    __tablename__ = "cart_items"

    __table_args__ = (

        # Prevent duplicate active listing rows inside same cart
        UniqueConstraint(
            "cart_id",
            "listing_id",
            name="uq_cart_listing"
        ),

        # Performance indexes
        Index("idx_cart_item_cart_id", "cart_id"),
        Index("idx_cart_item_listing_id", "listing_id"),
        Index("idx_cart_item_product_id", "product_id"),
        Index("idx_cart_item_market_id", "market_id"),
        Index("idx_cart_item_status", "status"),

        # Data integrity
        CheckConstraint("quantity > 0", name="ck_cart_item_quantity"),
        CheckConstraint("unit_price >= 0", name="ck_cart_item_unit_price"),
        CheckConstraint("market_fee >= 0", name="ck_cart_item_market_fee"),
        CheckConstraint("delivery_fee >= 0", name="ck_cart_item_delivery_fee"),
        CheckConstraint("total_price >= 0", name="ck_cart_item_total_price"),
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

    cart_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("carts.id", ondelete="CASCADE"),
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
    # CART SNAPSHOT
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

    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    total_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    # =========================================
    # STATE
    # =========================================

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active"
    )

    is_checked_out: Mapped[bool] = mapped_column(
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

    # =========================================
    # RELATIONSHIPS
    # =========================================

    cart = relationship(
        "Cart",
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