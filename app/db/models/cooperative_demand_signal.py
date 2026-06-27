import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from uuid import UUID
from sqlalchemy.dialects.postgresql import UUID as PGUUID



class CooperativeDemandSignal(Base):

    __tablename__ = "cooperative_demand_signals"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("market_products.id"),
        index=True
    )

    market_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("market_locations.id"),
        nullable=False,
        index=True
    )
        

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        index=True
    )

    signal_type: Mapped[str] = mapped_column(
        String(20)
    )
    # search | cart | join | purchase

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        Index("idx_coop_signal_product", "product_id"),
        Index("idx_coop_signal_market", "market_id"),
    )