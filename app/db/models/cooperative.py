import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Boolean,
    Numeric,
    ForeignKey,
    JSON,
    func,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Cooperative(Base):
    """
    Core Cooperative Entity (BushMarket Group Buying System)
    """

    __tablename__ = "cooperatives"

    __table_args__ = (
        Index("idx_cooperative_status", "status"),
        Index("idx_cooperative_creator", "creator_id"),
    )

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
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
    # PRODUCT SELECTION (MAX 3 enforced in service layer)
    # =========================
    product_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False
    )

    # =========================
    # TARGET SETTINGS
    # =========================
    target_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    max_members: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    current_members: Mapped[int] = mapped_column(Integer, default=0)

    target_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    contribution_per_member: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # =========================
    # LIFECYCLE
    # =========================
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",  # draft → active → funded → purchasing → closed
        index=True
    )

    # =========================
    # TIME CONSTRAINTS (SOFT-CODED RULES APPLY HERE)
    # =========================
    lifespan_days: Mapped[int] = mapped_column(Integer, nullable=False)

    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # =========================
    # ADMIN CONTROL FLAGS (SOFT CODED SYSTEM)
    # =========================
    discount_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # =========================
    # FINANCIAL CORE LINK
    # =========================
    pooled_wallet_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # =========================
    # FAILURE HANDLING
    # =========================
    auto_merge_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    partial_procurement_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # =========================
    # TIMESTAMPS
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
    # RELATIONSHIPS
    # =========================
    memberships = relationship(
        "CooperativeMembership",
        back_populates="cooperative",
        cascade="all, delete-orphan"
    )