import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    func,
    Index,
    CheckConstraint
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MarketVolatilityRule(Base):
    __tablename__ = "market_volatility_rules"

    __table_args__ = (
        CheckConstraint(
            "normal_threshold >= 0",
            name="ck_volatility_normal_threshold"
        ),
        CheckConstraint(
            "suspicious_threshold >= normal_threshold",
            name="ck_volatility_suspicious_threshold"
        ),
        CheckConstraint(
            "critical_threshold >= suspicious_threshold",
            name="ck_volatility_critical_threshold"
        ),
        Index("idx_volatility_market", "market_id"),
        Index("idx_volatility_product", "product_id"),
        Index("idx_volatility_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True
    )

    market_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_locations.id", ondelete="CASCADE"),
        nullable=True
    )

    normal_threshold: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=0.05,
        server_default="0.05"
    )

    suspicious_threshold: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=0.15,
        server_default="0.15"
    )

    critical_threshold: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=0.30,
        server_default="0.30"
    )

    sensitivity_multiplier: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=1.0,
        server_default="1.0"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    product = relationship(
        "Product",
        lazy="joined"
    )

    market = relationship(
        "MarketLocation",
        lazy="joined"
    )