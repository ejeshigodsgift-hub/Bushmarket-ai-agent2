# =========================================
# FILE: app/db/models/market_volatility_rule.py
# =========================================

import uuid

from sqlalchemy import (
    String,
    Float,
    Boolean,
    DateTime,
    func,
    Index
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketVolatilityRule(Base):

    __tablename__ = "market_volatility_rules"

    # =========================================
    # PRIMARY KEY
    # =========================================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # =========================================
    # SCOPE (OPTIONAL FILTERING)
    # =========================================
    product_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True
    )

    market_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True
    )

    # =========================================
    # THRESHOLDS
    # =========================================
    normal_threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.05
    )

    suspicious_threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.15
    )

    critical_threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.30
    )

    # =========================================
    # SENSITIVITY
    # =========================================
    sensitivity_multiplier: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0
    )

    # =========================================
    # STATUS
    # =========================================
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True
    )

    # =========================================
    # TIMESTAMPS
    # =========================================
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # =========================================
    # INDEXES (OPTIMIZED LOOKUPS)
    # =========================================
    __table_args__ = (
        Index(
            "idx_volatility_rule_scope",
            "product_id",
            "market_id",
            "is_active"
        ),
    )