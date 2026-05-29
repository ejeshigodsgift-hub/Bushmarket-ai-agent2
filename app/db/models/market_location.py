import uuid

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    func,
    Index,
    UniqueConstraint
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MarketLocation(Base):
    __tablename__ = "market_locations"

    __table_args__ = (
        UniqueConstraint(
            "name",
            "region_id",
            name="uq_market_location_name_region"
        ),
        Index("idx_market_location_region", "region_id"),
        Index("idx_market_location_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    region_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_regions.id", ondelete="RESTRICT"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    address: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )

    city: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )

    state: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )

    country: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="Nigeria",
        server_default="Nigeria"
    )

    latitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True
    )

    longitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
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

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    region = relationship(
        "MarketRegion",
        back_populates="markets",
        lazy="joined"
    )

    listings = relationship(
        "MarketProductListing",
        back_populates="market",
        lazy="selectin"
    )

    prices = relationship(
        "MarketProductPrice",
        back_populates="market",
        lazy="selectin"
    )