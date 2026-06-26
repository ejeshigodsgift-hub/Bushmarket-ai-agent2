import uuid
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Boolean,
    ForeignKey,
    func
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from sqlalchemy import ForeignKey


class SearchQuery(Base):
    __tablename__ = "search_queries"

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # USER CONTEXT
    # =========================
    user_id: Mapped[str] = mapped_column(
        String(36),
        index=True
    )

    # =========================
    # SEARCH CONTENT
    # =========================
    query_text: Mapped[str] = mapped_column(String, index=True)
    normalized_query: Mapped[str] = mapped_column(String, index=True)

    # =========================
    # SEARCH SOURCE (VERY IMPORTANT FOR AI LEARNING)
    # =========================
    search_source: Mapped[str] = mapped_column(
        String(30),
        default="manual"
    )
    # manual | ai | cooperative | voice

    # =========================
    # CONTEXT (BUSHMARKET MARKET INTELLIGENCE)
    # =========================
    market_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("market_locations.id"),
        nullable=True,
        index=True
    )

    user_lat: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_lng: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # =========================
    # RESULTS METADATA
    # =========================
    total_results: Mapped[int] = mapped_column(Integer, default=0)

    clicked_listing_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True
    )

    product_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("market_products.id"),
        nullable=True,
        index=True
    )

    # =========================
    # BEHAVIOR TRACKING (AI LEARNING LAYER)
    # =========================
    converted_to_cart: Mapped[bool] = mapped_column(Boolean, default=False)
    converted_to_purchase: Mapped[bool] = mapped_column(Boolean, default=False)

    # =========================
    # TIMESTAMP
    # =========================
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )