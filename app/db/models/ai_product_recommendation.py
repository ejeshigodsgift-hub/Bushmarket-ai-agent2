import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Numeric,
    func,
    Index,
    CheckConstraint,
    Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIProductRecommendation(Base):
    __tablename__ = "ai_product_recommendations"

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # AI CONTEXT
    # =========================
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    listing_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("market_product_listings.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # =========================
    # AI DECISION METRICS
    # =========================
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),  # e.g. 0.0000 - 1.0000
        nullable=False
    )

    rank_position: Mapped[int] = mapped_column(
        nullable=False,
        default=1
    )

    reasoning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    model_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # =========================
    # USER INTERACTION SIGNALS (AI LEARNING CORE)
    # =========================
    clicked: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    added_to_cart: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    purchased: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    # =========================
    # TIMESTAMP
    # =========================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # =========================
    # RELATIONSHIPS
    # =========================
    conversation = relationship(
        "AIConversation",
        lazy="selectin"
    )

    listing = relationship(
        "MarketProductListing",
        lazy="selectin"
    )

    # =========================
    # PERFORMANCE INDEXES
    # =========================
    __table_args__ = (
        Index("idx_ai_rec_conversation", "conversation_id"),
        Index("idx_ai_rec_listing", "listing_id"),
        Index("idx_ai_rec_score", "confidence_score"),

        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_confidence_range"
        ),
    )