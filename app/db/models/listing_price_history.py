import uuid

from sqlalchemy import (
    String,
    Float,
    ForeignKey,
    DateTime,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base


class ListingPriceHistory(Base):

    __tablename__ = "listing_price_history"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    listing_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_product_listings.id"),
        nullable=False,
        index=True
    )

    old_price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    new_price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    updated_by_agent_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )