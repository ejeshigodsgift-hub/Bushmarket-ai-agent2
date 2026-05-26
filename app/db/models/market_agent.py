import uuid

from sqlalchemy import (
    String,
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


class MarketAgent(Base):
    __tablename__ = "market_agents"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    assigned_market_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("market_locations.id"),
        nullable=True
    )

    is_verified_agent: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending"
    )
    # pending | approved | suspended

    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship("User")
    market = relationship("MarketLocation")