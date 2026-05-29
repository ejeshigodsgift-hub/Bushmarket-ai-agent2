# =========================================
# FILE: app/db/models/listing_agent_activity.py
# =========================================

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    JSON,
    func
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class ListingAgentActivity(Base):

    __tablename__ = "listing_agent_activities"

    # =========================================
    # PRIMARY KEY
    # =========================================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # =========================================
    # LISTING REFERENCE
    # =========================================
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "market_product_listings.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # =========================================
    # AGENT REFERENCE
    # aligned with market_agents system
    # =========================================
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "market_agents.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # =========================================
    # ACTIVITY ACTION
    # =========================================
    action: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True
    )

    # supported:
    # listing_created
    # listing_updated
    # listing_published
    # listing_disabled
    # inventory_updated
    # inventory_reserved
    # inventory_released
    # inventory_sold
    # price_changed

    # =========================================
    # OPTIONAL EVENT METADATA
    # supports Kafka / Redis / Audit expansion
    # =========================================
    metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    # =========================================
    # IP / TRACEABILITY
    # =========================================
    ip_address: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # =========================================
    # EVENT TIMESTAMP
    # =========================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    # =========================================
    # RELATIONSHIPS
    # =========================================
    listing = relationship(
        "MarketProductListing",
        back_populates="agent_activities",
        lazy="selectin"
    )

    agent = relationship(
        "MarketAgent",
        lazy="selectin"
    )

    # =========================================
    # TABLE CONFIG
    # =========================================
    __table_args__ = (

        # prevent empty actions
        CheckConstraint(
            "length(action) >= 3",
            name="chk_listing_agent_activity_action"
        ),

        # performance indexes
        Index(
            "idx_listing_agent_activity_listing_created",
            "listing_id",
            "created_at"
        ),

        Index(
            "idx_listing_agent_activity_agent_created",
            "agent_id",
            "created_at"
        ),

        Index(
            "idx_listing_agent_activity_action_created",
            "action",
            "created_at"
        ),
    )