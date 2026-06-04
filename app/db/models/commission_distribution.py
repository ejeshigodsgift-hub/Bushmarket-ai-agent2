import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    func,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class CommissionDistribution(Base):

    __tablename__ = "commission_distributions"

    __table_args__ = (
        Index("idx_commission_order", "order_id"),
        Index("idx_commission_order_item", "order_item_id"),
        Index("idx_commission_status", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )

    order_item_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False
    )

    gross_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    seller_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    platform_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    market_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    agent_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending"
    )
    # pending | settled | failed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    order = relationship("Order")

    order_item = relationship("OrderItem")