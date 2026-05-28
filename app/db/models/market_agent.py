import uuid

from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    Integer,
    func,
    CheckConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class MarketAgent(Base):

    __tablename__ = "market_agents"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'suspended')",
            name="chk_market_agent_status"
        ),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False,
        index=True
    )

    assigned_market_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("market_locations.id"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
        index=True
    )

    is_verified_agent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    rating: Mapped[float] = mapped_column(
        Numeric(3, 2),
        default=0.0,
        nullable=False
    )

    total_tasks: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    region: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    user = relationship("User")
    market = relationship("MarketLocation")