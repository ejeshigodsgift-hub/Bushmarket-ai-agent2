import uuid

from sqlalchemy import (
    String,
    Float,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class MarketProductPrice(Base):

    __tablename__ = "market_product_prices"

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

    price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    market_fee: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    volatility_score: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    updated_by_agent_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("users.id"),
        nullable=True
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    market = relationship(
        "MarketLocation",
        back_populates="prices"
    )