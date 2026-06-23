# =========================================
# FILE: app/db/models/listing_admin_activity.py
# =========================================

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    func,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ListingAdminActivity(Base):
    __tablename__ = "listing_admin_activities"

    __table_args__ = (
        Index("idx_admin_activity_listing", "listing_id"),
        Index("idx_admin_activity_admin", "admin_id"),
        Index("idx_admin_activity_action", "action_type"),
    )

    ALLOWED_ACTIONS = (
        "listing_published",
        "inventory_updated",
        "admin_approved",
        "admin_rejected",
    )

    # =========================================
    # PRIMARY KEY
    # =========================================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================================
    # CORE RELATIONS
    # =========================================
    listing_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("market_product_listings.id", ondelete="CASCADE"),
        nullable=False
    )

    admin_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True
    )

    # =========================================
    # ACTION METADATA
    # =========================================
    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    activity_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    is_system_generated: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # =========================================
    # TIMESTAMP
    # =========================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # =========================================
    # RELATIONSHIPS
    # =========================================
    listing = relationship(
        "MarketProductListing",
        backref="ListingAdminActivity",
        lazy="selectin"
    )

    admin = relationship(
        "User",
        lazy="selectin"
    )