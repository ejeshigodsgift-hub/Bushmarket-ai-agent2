import uuid

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    func,
    Index,
    UniqueConstraint
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MarketRegion(Base):
    __tablename__ = "market_regions"

    __table_args__ = (
        UniqueConstraint("code", name="uq_market_region_code"),
        UniqueConstraint("name", name="uq_market_region_name"),
        Index("idx_market_region_is_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
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

    markets = relationship(
        "MarketLocation",
        back_populates="region",
        lazy="selectin"
    )