import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
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


class MeasurementUnit(Base):

    __tablename__ = "measurement_units"

    __table_args__ = (
        UniqueConstraint("code", name="uq_measurement_units_code"),
        UniqueConstraint("name", name="uq_measurement_units_name"),
        Index("idx_measurement_units_code", "code"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
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

    products = relationship(
        "ProductMeasurement",
        back_populates="measurement_unit",
        cascade="all, delete-orphan",
        lazy="selectin"
    )