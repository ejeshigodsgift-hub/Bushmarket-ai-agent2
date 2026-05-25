import uuid

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class MarketRegion(Base):

    __tablename__ = "market_regions"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    name: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
        index=True
    )

    state: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )

    country: Mapped[str] = mapped_column(
        String(120),
        default="Nigeria"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    markets = relationship(
        "MarketLocation",
        back_populates="region"
    )