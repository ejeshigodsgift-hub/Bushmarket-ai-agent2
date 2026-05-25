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
    mapped_column
)

from app.db.base import Base


class MarketProductMeasurement(Base):

    __tablename__ = "market_product_measurements"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    market_product_price_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_product_prices.id"),
        nullable=False,
        index=True
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

    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )