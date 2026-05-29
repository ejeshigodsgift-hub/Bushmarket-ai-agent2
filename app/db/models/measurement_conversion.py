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
    mapped_column
)

from app.db.base import Base


class MeasurementConversion(Base):

    __tablename__ = "measurement_conversions"

    __table_args__ = (
        UniqueConstraint(
            "from_measurement_unit_id",
            "to_measurement_unit_id",
            name="uq_measurement_conversion"
        ),
        Index(
            "idx_measurement_conversion_from",
            "from_measurement_unit_id"
        ),
        Index(
            "idx_measurement_conversion_to",
            "to_measurement_unit_id"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    from_measurement_unit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("measurement_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    to_measurement_unit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("measurement_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    conversion_factor: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False
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