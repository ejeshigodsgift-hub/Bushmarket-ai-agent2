import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Integer,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    cart_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    listing_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_listings.id"),
        nullable=False,
        index=True
    )

    product_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_products.id"),
        nullable=False
    )

    market_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_locations.id"),
        nullable=False
    )

    measurement_unit_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("measurement_units.id"),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    unit_price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    market_fee: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    total_price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    cart = relationship(
        "Cart",
        back_populates="items"
    )