import uuid

from sqlalchemy import (
    String,
    Float,
    Integer,
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
        nullable=False
    )

    listing_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_listings.id"),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    unit_price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    gate_fee: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    total_price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    cart = relationship("Cart")
    listing = relationship("MarketListing")