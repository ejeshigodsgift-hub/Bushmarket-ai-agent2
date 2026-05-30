import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Float,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    func,
    Index,
    UniqueConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class MarketProductMeasurement(Base):

    __tablename__ = "market_product_measurements"

    __table_args__ = (
        Index("idx_measurement_market_price", "market_price_id"),
        Index("idx_measurement_unit", "measurement_unit_id"),

        UniqueConstraint(
            "market_price_id",
            "measurement_unit_id",
            name="uq_market_price_measurement_unit"
        ),
    )

    # =====================================================
    # PRIMARY KEY
    # =====================================================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =====================================================
    # FOREIGN KEYS
    # =====================================================

    market_price_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("market_prices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    measurement_unit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("measurement_units.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # =====================================================
    # MEASUREMENT DATA
    # =====================================================

    price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    # =====================================================
    # TIMESTAMP
    # =====================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    market_price = relationship(
        "MarketPrice",
        backref="measurements",
        lazy="joined"
    )

    measurement_unit = relationship(
        "MeasurementUnit",
        backref="market_price_measurements",
        lazy="joined"
    )