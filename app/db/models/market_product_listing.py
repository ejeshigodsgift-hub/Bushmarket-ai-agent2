import uuid

from decimal import Decimal
from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    Integer,
    func,
    Index,
    CheckConstraint,
    Text,
    UniqueConstraint
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class MarketProductListing(Base):
    __tablename__ = "market_product_listings"

    __table_args__ = (
        Index("idx_listing_market", "market_id"),
        Index("idx_listing_product", "product_id"),
        Index("idx_listing_agent", "assigned_agent_id"),
        Index("idx_listing_status", "status"),

        UniqueConstraint(
            "market_id",
            "product_id",
            "variant_id",
            "measurement_unit_id",
            name="uq_market_product_variant_unit"
        ),

        CheckConstraint(
            "unit_price > 0",
            name="ck_listing_positive_price"
        ),

        CheckConstraint(
            "available_stock >= 0",
            name="ck_listing_non_negative_stock"
        ),

        CheckConstraint(
            "reserved_stock >= 0",
            name="ck_listing_non_negative_reserved_stock"
        ),

        CheckConstraint(
            "sold_stock >= 0",
            name="ck_listing_non_negative_sold_stock"
        ),

        CheckConstraint(
            "status IN ('draft','active','disabled','sold_out')",
            name="ck_listing_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "market_locations.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "market_products.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "product_variants.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    measurement_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "measurement_units.id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    market_fee: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0"
    )

    available_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    reserved_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    sold_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
        server_default="draft"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )


    # ====================================
# COMMISSION SNAPSHOTS
# ====================================

    platform_fee_percent: Mapped[Decimal]    
= mapped_column(
        Numeric(8, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0"
    )

    market_fee_percent: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0"
    )

    agent_fee_percent: Mapped[Decimal] =  mapped_column(
        Numeric(8, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0"
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    market = relationship(
        "MarketLocation",
        back_populates="listings",
        lazy="joined"
    )

    product = relationship(
        "Product",
        back_populates="market_product_listings",
        lazy="joined"
    )

    variant = relationship(
        "ProductVariant",
        back_populates="market_product_listings",
        lazy="joined"
    )

    measurement_unit = relationship(
        "MeasurementUnit",
        back_populates="market_product_listings",
        lazy="joined"
    )

    assigned_agent = relationship(
        "User",
        back_populates="market_product_listings",
        lazy="joined"
    )
    
    agent_activities = relationship(
         "ListingAgentActivity",
         back_populates="listing",
         lazy="selectin",
         cascade="all, delete-orphan"
    )

    inventory = relationship(
        "Inventory",
        back_populates="listing",
        uselist=False,
        lazy="selectin"
    )

    cart_items = relationship(
        "CartItem",
        back_populates="listing",
        lazy="selectin"
    )

    checkout_items = relationship(
        "CheckoutItem",
        back_populates="listing",
        lazy="selectin"
    )

    order_items = relationship(
        "OrderItem",
        back_populates="listing",
        lazy="selectin"
    )

    price_histories = relationship(
        "ListingPriceHistory",
        back_populates="listing",
        lazy="selectin",
        cascade="all, delete-orphan"
    )