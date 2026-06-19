import uuid

from sqlalchemy import (
    String,
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


class Cart(Base):
    __tablename__ = "carts"

    __table_args__ = (
        Index("idx_cart_user", "user_id"),
        Index("idx_cart_status", "status"),
        Index("idx_cart_created", "created_at"),

        CheckConstraint(
            "status IN ("
            "'active',"
            "'checkout_locked',"
            "'checked_out',"
            "'expired'"
            ")",
            name="ck_cart_status"
        ),

        CheckConstraint(
            "subtotal_amount >= 0",
            name="ck_cart_subtotal_amount"
        ),
        CheckConstraint(
            "total_market_fee >= 0",
            name="ck_cart_market_fee"
        ),
        CheckConstraint(
            "total_delivery_fee >= 0",
            name="ck_cart_delivery_fee"
        ),
        CheckConstraint(
            "total_amount >= 0",
            name="ck_cart_total_amount"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
        server_default="active"
    )

    subtotal_amount: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=0,
        server_default="0"
    )

    total_market_fee: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=0,
        server_default="0"
    )

    total_delivery_fee: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=0,
        server_default="0"
    )

    total_amount: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=0,
        server_default="0"
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="NGN",
        server_default="NGN"
    )

    is_checked_out: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false"
    )

    expires_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    checked_out_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
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

    user = relationship(
        "User",
        lazy="joined"
    )

    items = relationship(
        "CartItem",
        back_populates="cart",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    checkout = relationship(
        "Checkout",
        back_populates="cart",
        uselist=False,
        lazy="selectin"
    )