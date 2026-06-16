import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Numeric,
    func,
    CheckConstraint,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base


class PlatformSettings(Base):
    """
    Global BushMarket configuration.

    Only one active row should normally exist.
    Admin dashboard updates this record.
    """

    __tablename__ = "platform_settings"

    __table_args__ = (

        Index("idx_platform_settings_active", "is_active"),

        # =========================
        # FEES VALIDATION
        # =========================
        CheckConstraint("platform_fee_percent >= 0", name="ck_platform_fee_percent"),
        CheckConstraint("agent_fee_percent >= 0", name="ck_agent_fee_percent"),
        CheckConstraint("cooperative_fee_percent >= 0", name="ck_cooperative_fee_percent"),
        CheckConstraint("minimum_platform_fee >= 0", name="ck_minimum_platform_fee"),
        CheckConstraint("maximum_platform_fee >= 0", name="ck_maximum_platform_fee"),

        # =========================
        # PRODUCT RULES
        # =========================
        CheckConstraint("min_products >= 0", name="ck_min_products"),
        CheckConstraint("max_products >= min_products", name="ck_max_products"),

        # =========================
        # MEMBERSHIP RULES
        # =========================
        CheckConstraint("min_members >= 1", name="ck_min_members"),
        CheckConstraint("max_members >= min_members", name="ck_max_members"),

        # =========================
        # LIFESPAN RULES
        # =========================
        CheckConstraint("min_lifespan_days >= 1", name="ck_min_lifespan"),
        CheckConstraint("max_lifespan_days >= min_lifespan_days", name="ck_max_lifespan"),
    )

    # ====================================
    # PRIMARY KEY
    # ====================================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # ====================================
    # PLATFORM COMMISSIONS
    # ====================================
    platform_fee_percent: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        default=Decimal("5.00")
    )

    agent_fee_percent: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        default=Decimal("2.00")
    )

    cooperative_fee_percent: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        default=Decimal("1.00")
    )

    minimum_platform_fee: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    maximum_platform_fee: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    # ====================================
    # PRODUCT LIMITS (NEW)
    # ====================================
    min_products: Mapped[int] = mapped_column(
        nullable=False,
        default=1
    )

    max_products: Mapped[int] = mapped_column(
        nullable=False,
        default=3
    )

    # ====================================
    # MEMBERSHIP LIMITS (NEW)
    # ====================================
    min_members: Mapped[int] = mapped_column(
        nullable=False,
        default=1
    )

    max_members: Mapped[int] = mapped_column(
        nullable=False,
        default=30
    )

    # ====================================
    # LIFESPAN LIMITS (NEW)
    # ====================================
    min_lifespan_days: Mapped[int] = mapped_column(
        nullable=False,
        default=10
    )

    max_lifespan_days: Mapped[int] = mapped_column(
        nullable=False,
        default=60
    )


    # =========================
# EXTENSION RULES (MISSING)
# =========================
    min_extension_days: Mapped[int] = mapped_column(
        nullable=False,
        default=1
    )

    max_extension_days: Mapped[int] = mapped_column(
        nullable=False,
        default=7
    )

    default_extension_days: Mapped[int] =   mapped_column(
        nullable=False,
        default=3
    )


    # ====================================
    # FEATURE FLAGS
    # ====================================
    is_fee_system_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    # ====================================
    # AUDIT
    # ====================================
    updated_by: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # ====================================
    # TIMESTAMPS
    # ====================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )