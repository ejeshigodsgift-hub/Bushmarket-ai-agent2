import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    func
)

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ListingIntelligenceScore(Base):

    __tablename__ = "listing_intelligence_scores"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    listing_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("market_product_listings.id"),
        unique=True,
        index=True
    )

    market_score: Mapped[float] = mapped_column(
        Numeric(10,4),
        default=0
    )

    demand_score: Mapped[float] = mapped_column(
        Numeric(10,4),
        default=0
    )

    inventory_score: Mapped[float] = mapped_column(
        Numeric(10,4),
        default=0
    )

    distance_score: Mapped[float] = mapped_column(
        Numeric(10,4),
        default=0
    )

    sales_score: Mapped[float] = mapped_column(
        Numeric(10,4),
        default=0
    )

    recommendation_score: Mapped[float] = mapped_column(
        Numeric(10,4),
        default=0
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )