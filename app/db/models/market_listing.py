import uuid

from sqlalchemy import (
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


class MarketListing(Base):
    __tablename__ = "market_listings"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    product_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_products.id"),
        nullable=False,
        index=True
    )

    market_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_locations.id"),
        nullable=False,
        index=True
    )

    assigned_agent_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_agents.id"),
        nullable=False
    )

    measurement_unit_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("measurement_units.id"),
        nullable=False
    )

    variant_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    unit_price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    available_stock: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    gate_fee: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="draft"
    )
    # draft | active | disabled

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    product = relationship("MarketProduct")
    market = relationship("MarketLocation")
    unit = relationship("MeasurementUnit")
    agent = relationship("MarketAgent")