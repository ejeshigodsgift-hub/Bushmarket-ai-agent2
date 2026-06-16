import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Boolean,
    Numeric,
    ForeignKey,
    JSON,
    func,
    Index,
    Text
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Cooperative(Base):
    """
    Core Cooperative Entity (BushMarket Group Buying Engine)
    """

    __tablename__ = "cooperatives"

    __table_args__ = (
        Index("idx_cooperative_status", "status"),
        Index("idx_cooperative_creator", "creator_id"),
        Index("idx_cooperative_market", "market_id"),
    )

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # BASIC INFO
    # =========================
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # =========================
    # MARKET CONTEXT
    # =========================
    market_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_locations.id"),
        nullable=False,
        index=True
    )

    # =========================
    # CREATOR
    # =========================
    creator_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # =========================
    # PRODUCTS (MAX 3 enforced in service/engine)
    # =========================
    product_ids: Mapped[list] = mapped_column(JSON, nullable=False)

    # =========================
    # TARGET CONFIG
    # =========================
    target_quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    target_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    contribution_per_member: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    max_members: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    current_members: Mapped[int] = mapped_column(Integer, default=0)

    # =========================
    # LIFECYCLE (CRITICAL)
    # =========================
    status: Mapped[str] = mapped_column(
        String(30),
        default="draft",
        index=True
    )
    """ 
    draft
    active
    extension_vote
    partial_vote
    merge_vote
    funded
    procurement_pending
    purchasing
    delivered
    closed
    expired
    cancelled
    refunded

    """

    # =========================
    # TIMING RULES
    # =========================
    lifespan_days: Mapped[int] = mapped_column(Integer, nullable=False)

    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # =========================
    # BUSINESS RULE FLAGS (ADMIN CONTROLLED / SOFT CODED)
    # =========================
    discount_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    partial_procurement_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    auto_merge_allowed: Mapped[bool] = mapped_column(Boolean, default=True)

    # =========================
    # FINANCIAL CORE (ESCROW SYSTEM READY)
    # =========================
    pooled_wallet_id: Mapped[str | None] = mapped_column(String, nullable=True)

    escrow_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    total_contributed: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # =========================
    # FAILURE HANDLING
    # =========================
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # =========================
    # LIFECYCLE TIMESTAMPS
    # =========================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


    # =========================
# LIFECYCLE (CRITICAL)
# ========================

    current_extension_round: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )

    funded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    purchasing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # =========================
    # RELATIONSHIPS
    # =========================
    memberships = relationship(
        "CooperativeMembership",
        back_populates="cooperative",
        cascade="all, delete-orphan"
    )

    creator = relationship("User", lazy="selectin")

    market = relationship("MarketLocation", lazy="selectin")