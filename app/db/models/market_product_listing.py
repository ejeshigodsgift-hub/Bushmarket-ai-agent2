import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Float,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class MarketProductListing(Base):

    __tablename__ = "market_product_listings"

    # =========================
    # PRIMARY ID
    # =========================
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # MARKET RELATIONS
    # =========================
    market_id: Mapped[str] = mapped_column(
        String,
        ForeignKey(
            "market_locations.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    product_id: Mapped[str] = mapped_column(
        String,
        ForeignKey(
            "products.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    variant_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey(
            "product_variants.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    measurement_unit_id: Mapped[str] = mapped_column(
        String,
        ForeignKey(
            "measurement_units.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    assigned_agent_id: Mapped[str] = mapped_column(
        String,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # =========================
    # LISTING CONTENT
    # =========================
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # =========================
    # PRICING
    # =========================
    unit_price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    market_fee: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False
    )

    volatility_score: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False
    )

    # =========================
    # STOCK MANAGEMENT
    # =========================
    available_stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    reserved_stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    minimum_order_quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )

    # =========================
    # MARKETPLACE FLAGS
    # =========================
    cooperative_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    ai_visible: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

    # =========================
    # LISTING STATUS
    # =========================
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False,
        index=True
    )
    # VALID:
    # draft
    # active
    # disabled

    # =========================
    # TIMESTAMPS
    # =========================
    last_price_update_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

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
    market = relationship(
        "MarketLocation",
        backref="product_listings"
    )

    product = relationship(
        "Product",
        backref="market_listings"
    )

    variant = relationship(
        "ProductVariant",
        backref="market_listings"
    )

    measurement_unit = relationship(
        "MeasurementUnit",
        backref="market_listings"
    )

    assigned_agent = relationship(
        "User",
        backref="market_product_listings"
    )