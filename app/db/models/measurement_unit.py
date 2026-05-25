import uuid

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Float,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class MeasurementUnit(Base):

    __tablename__ = "measurement_units"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # per bag
    # per kg
    # per tuber
    # per gallon

    name: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
        index=True
    )

    slug: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False
    )

    symbol: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    # weight
    # liquid
    # quantity
    # tuber
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # allows AI & conversion system
    base_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    product_measurements = relationship(
        "ProductMeasurement",
        back_populates="measurement_unit"
    )