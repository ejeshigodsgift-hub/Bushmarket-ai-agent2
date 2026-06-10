from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CooperativePartialProcurementProposal(Base):
    __tablename__ = "cooperative_partial_procurement_proposals"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    cooperative_id: Mapped[str] = mapped_column(String, index=True)
    listing_id: Mapped[str] = mapped_column(String)

    requested_quantity: Mapped[int] = mapped_column(Integer)
    available_quantity: Mapped[int] = mapped_column(Integer)

    total_cost: Mapped[float] = mapped_column(Numeric(18, 2))

    status: Mapped[str] = mapped_column(String, default="pending")
    # pending | voting | approved | rejected | executed

    approval_threshold: Mapped[int] = mapped_column(Integer, default=100)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)