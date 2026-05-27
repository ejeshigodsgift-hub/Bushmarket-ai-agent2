import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Numeric,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Checkout(Base):

    __tablename__ = "checkouts"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id"),
        index=True
    )

    cart_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("carts.id"),
        unique=True
    )

    subtotal: Mapped[float] = mapped_column(Numeric(12, 2))
    market_fee_total: Mapped[float] = mapped_column(Numeric(12, 2))
    delivery_fee: Mapped[float] = mapped_column(Numeric(12, 2))
    total: Mapped[float] = mapped_column(Numeric(12, 2))

    status: Mapped[str] = mapped_column(
        String,
        default="initiated",
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )