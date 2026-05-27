import uuid

from sqlalchemy import (
    String,
    ForeignKey,
    Numeric,
    Integer
)

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CheckoutItem(Base):

    __tablename__ = "checkout_items"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    checkout_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("checkouts.id")
    )

    listing_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_listings.id")
    )

    product_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_products.id")
    )

    market_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_locations.id")
    )

    quantity: Mapped[int] = mapped_column(Integer)

    unit_price: Mapped[float] = mapped_column(Numeric(12, 2))
    market_fee: Mapped[float] = mapped_column(Numeric(12, 2))
    total_price: Mapped[float] = mapped_column(Numeric(12, 2))