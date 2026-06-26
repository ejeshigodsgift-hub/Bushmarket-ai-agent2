import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Numeric,
    func,
    Index,
    CheckConstraint,
    Text,
    Boolean
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
    # CONTEXT
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
    # AI SCORES
    # =========================
    confidence_score: Mapped[float] = mapped_column(
        Numeric(5, 4),  # 0.0000 - 1.0000
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
    # USER FEEDBACK LOOP
    # =========================
    clicked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    added_to_cart: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    purchased: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )


    impression_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    click_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    cart_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    purchase_count: Mapped[int] = mapped_column(
        default=0,
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
    # INDEXES + CONSTRAINTS
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