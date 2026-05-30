import uuid
from datetime import datetime

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


class MarketPrice(Base):
    __tablename__ = "market_prices"

    __table_args__ = (
        Index("idx_market_price_market", "market_id"),
        Index("idx_market_price_product", "product_id"),
        Index("idx_market_price_variant", "variant_id"),
        Index("idx_market_price_unit", "measurement_unit_id"),
        Index("idx_market_price_created", "created_at"),

        CheckConstraint(
            "unit_price > 0",
            name="ck_market_price_positive"
        ),
    )

    # =====================================================
    # PRIMARY KEY
    # =====================================================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # =====================================================
    # FOREIGN KEYS (CLEAN + CONSISTENT)
    # =====================================================

    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_locations.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_products.id", ondelete="CASCADE"),
        nullable=False
    )

    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True
    )

    measurement_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("measurement_units.id", ondelete="RESTRICT"),
        nullable=False
    )

    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # =====================================================
    # PRICE DATA
    # =====================================================

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

    # =====================================================
    # STATUS
    # =====================================================

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    market = relationship(
        "MarketLocation",
        back_populates="market_prices",
        lazy="joined"
    )

    product = relationship(
        "Product",
        back_populates="market_prices",
        lazy="joined"
    )

    variant = relationship(
        "ProductVariant",
        lazy="joined"
    )

    measurement_unit = relationship(
        "MeasurementUnit",
        lazy="joined"
    )