# app/db/models/product_recommendation_feature.py

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Numeric,
    func,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base


class ProductRecommendationFeature(Base):

    __tablename__ = "product_recommendation_features"

    __table_args__ = (
        Index(
            "idx_product_rec_feature_listing",
            "listing_id"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    listing_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "market_product_listings.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False
    )

    demand_score: Mapped[float] = mapped_column(
        Numeric(10, 4),
        default=0
    )

    popularity_score: Mapped[float] = mapped_column(
        Numeric(10, 4),
        default=0
    )

    click_score: Mapped[float] = mapped_column(
        Numeric(10, 4),
        default=0
    )

    cart_score: Mapped[float] = mapped_column(
        Numeric(10, 4),
        default=0
    )

    purchase_score: Mapped[float] = mapped_column(
        Numeric(10, 4),
        default=0
    )

    inventory_score: Mapped[float] = mapped_column(
        Numeric(10, 4),
        default=0
    )

    distance_score: Mapped[float] = mapped_column(
        Numeric(10, 4),
        default=0
    )

    final_score: Mapped[float] = mapped_column(
        Numeric(10, 4),
        default=0
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )