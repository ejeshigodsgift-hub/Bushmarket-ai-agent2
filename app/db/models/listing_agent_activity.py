import uuid

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

    # =====================================================
    # PRIMARY KEY
    # =====================================================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # =====================================================
    # CORE REFERENCES (ALIGNED SYSTEM-WIDE)
    # =====================================================

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "market_product_listings.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # IMPORTANT:
    # This is ALWAYS users.id (agent, admin, shopper actor)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================================
    # ACTION TRACKING
    # =====================================================
    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    # examples:
    # listing_created
    # listing_published
    # inventory_updated
    # price_changed
    # order_placed (optional reuse)
    # cart_updated (optional reuse)

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

    # system vs human action
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
        lazy="joined",
        backref="agent_activities"
    )

    agent = relationship(
        "User",
        lazy="joined"
    )