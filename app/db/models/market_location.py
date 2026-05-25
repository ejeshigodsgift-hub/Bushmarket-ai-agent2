import uuid

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
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


class MarketLocation(Base):

    __tablename__ = "market_locations"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    region_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_regions.id"),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True
    )

    slug: Mapped[str] = mapped_column(
        String(180),
        unique=True,
        nullable=False
    )

    address: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    live_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    region = relationship(
        "MarketRegion",
        back_populates="markets"
    )

    prices = relationship(
        "MarketProductPrice",
        back_populates="market"
    )