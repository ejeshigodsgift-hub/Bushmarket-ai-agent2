import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Boolean,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class Order(Base):

    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    cooperative_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True
    )

    order_number: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    subtotal_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    market_fee_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    delivery_fee_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    total_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String,
        default="NGN"
    )

    payment_status: Mapped[str] = mapped_column(
        String,
        default="pending",
        index=True
    )

    status: Mapped[str] = mapped_column(
        String,
        default="pending",
        index=True
    )

    is_cooperative_order: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )