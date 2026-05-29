import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    func,
    UniqueConstraint,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class ProductMeasurement(Base):

    __tablename__ = "product_measurements"

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "measurement_unit_id",
            name="uq_product_measurement"
        ),
        Index("idx_product_measurement_product", "product_id"),
        Index("idx_product_measurement_unit", "measurement_unit_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("market_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    measurement_unit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("measurement_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    conversion_factor: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
        default=1
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True
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

    product = relationship(
        "Product",
        back_populates="measurements",
        lazy="joined"
    )

    measurement_unit = relationship(
        "MeasurementUnit",
        back_populates="products",
        lazy="joined"
    )