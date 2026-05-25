import uuid

from sqlalchemy import (
    String,
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


class ProductMeasurement(Base):

    __tablename__ = "product_measurements"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    product_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("products.id"),
        nullable=False
    )

    measurement_unit_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("measurement_units.id"),
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    product = relationship(
        "Product",
        back_populates="measurements"
    )

    measurement_unit = relationship(
        "MeasurementUnit"
    )