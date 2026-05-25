import uuid

from sqlalchemy import (
    String,
    Float,
    Boolean,
    DateTime,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base


class MarketFeeRule(Base):

    __tablename__ = "market_fee_rules"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False
    )

    fee_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    is_percentage: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )