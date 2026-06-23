import uuid
from fastapi import HTTPException

from sqlalchemy.orm import validates
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Boolean,
    func,
    Index,
    Text
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ListingAgentActivity(Base):
    __tablename__ = "listing_agent_activities"

    __table_args__ = (
        Index("idx_listing_activity_listing", "listing_id"),
        Index("idx_listing_activity_user", "agent_id"),
        Index("idx_listing_activity_action", "action_type"),
        Index("idx_listing_activity_created", "created_at"),
    )

    ALLOWED_ACTIONS = (
        "draft_created",
        "submitted_for_review"
        
    )

    # =====================================================
    # PRIMARY KEY
    # =====================================================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # =====================================================
    # CORE REFERENCES
    # =====================================================
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_product_listings.id", ondelete="CASCADE"),
        nullable=False
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # =====================================================
    # ACTION TYPE (define FIRST)
    # =====================================================
    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    @validates("action_type")
    def validate_action_type(self, key, value):
        if value not in self.ALLOWED_ACTIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action_type: {value}"
            )
        return value

    # =====================================================
    # ACTION TRACKING
    # =====================================================
    activity_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # =====================================================
    # TRACEABILITY
    # =====================================================
    ip_address: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    device_info: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    is_system_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false"
    )

    # =====================================================
    # TIMESTAMP
    # =====================================================
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================
    listing = relationship(
        "MarketProductListing",
        back_populates="listing_activities",
        lazy="joined"
    )

    agent = relationship(
        "User",
        back_populates="listing_activities",
        lazy="joined"
    )