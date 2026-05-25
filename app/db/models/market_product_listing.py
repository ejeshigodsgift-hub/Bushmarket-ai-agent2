import uuid

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

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    market_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_locations.id"),
        nullable=False,
        index=True
    )

    product_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("products.id"),
        nullable=False,
        index=True
    )

    variant_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("product_variants.id"),
        nullable=True
    )

    measurement_unit_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("measurement_units.id"),
        nullable=False
    )

    assigned_agent_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    unit_price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    market_fee: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    available_stock: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    reserved_stock: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    minimum_order_quantity: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    cooperative_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    ai_visible: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    volatility_score: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    last_price_update_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )