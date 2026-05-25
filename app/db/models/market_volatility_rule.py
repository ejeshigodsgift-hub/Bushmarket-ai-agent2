import uuid
from sqlalchemy import (
    String, Float, Boolean, ForeignKey, DateTime, func
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketVolatilityRule(Base):
    __tablename__ = "market_volatility_rules"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Scope control (VERY IMPORTANT)
    product_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    market_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    # Thresholds (admin controlled)
    normal_threshold: Mapped[float] = mapped_column(Float, default=0.05)
    suspicious_threshold: Mapped[float] = mapped_column(Float, default=0.15)
    critical_threshold: Mapped[float] = mapped_column(Float, default=0.30)

    # Optional sensitivity tuning
    sensitivity_multiplier: Mapped[float] = mapped_column(Float, default=1.0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())