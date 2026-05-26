import uuid

from sqlalchemy import (
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    subtotal: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    total_gate_fee: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    total_amount: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    is_checked_out: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship("User")