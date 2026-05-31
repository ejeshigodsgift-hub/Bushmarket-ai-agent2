import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Numeric,
    Text,
    func,
    Index,
    UniqueConstraint
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Product(Base):
    __tablename__ = "market_products"

    __table_args__ = (
        UniqueConstraint("slug", name="uq_market_products_slug"),
        Index("idx_market_products_name", "name"),
        Index("idx_market_products_category", "category"),
    )

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # CORE PRODUCT FIELDS
    # =========================
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    category: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True
    )

    image_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    base_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    sku: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        unique=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

    # =========================
    # TIMESTAMPS
    # =========================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # =========================
    # RELATIONSHIPS
    # =========================

    variants = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    measurements = relationship(
        "ProductMeasurement",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    inventories = relationship(
        "Inventory",
        back_populates="product",
        lazy="selectin"
    )

    # 🔥 THIS FIXES YOUR MARKET PRODUCT LISTING ALIGNMENT
    market_product_listings = relationship(
        "MarketProductListing",
        back_populates="product",
        lazy="selectin"
    )


    market_prices = relationship(
        "MarketPrice",
        back_populates="product",
        cascade="all, delete-orphan"
    )