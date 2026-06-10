from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CooperativePartialVote(Base):
    __tablename__ = "cooperative_partial_votes"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    proposal_id: Mapped[str] = mapped_column(String, index=True)
    member_id: Mapped[str] = mapped_column(String, index=True)

    vote: Mapped[bool] = mapped_column(Boolean)  # True = approve, False = reject

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)