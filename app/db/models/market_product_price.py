import uuid

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    func,
    Index,
    CheckConstraint
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MarketProductPrice(Base):
    __tablename__ = "market_product_prices"

    __table_args__ = (
        Index("idx_market_product_price_market", "market_id"),
        Index("idx_market_product_price_product", "product_id"),
        Index("idx_market_product_price_created", "created_at"),
        CheckConstraint(
            "unit_price > 0",
            name="ck_market_product_price_positive"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_locations.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    measurement_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("measurement_units.id", ondelete="RESTRICT"),
        nullable=False
    )

    unit_price: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    price_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="listing",
        server_default="listing"
    )

    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    market = relationship(
        "MarketLocation",
        back_populates="prices",
        lazy="joined"
    )

    product = relationship(
        "Product",
        lazy="joined"
    )

    measurement_unit = relationship(
        "MeasurementUnit",
        lazy="joined"
    )