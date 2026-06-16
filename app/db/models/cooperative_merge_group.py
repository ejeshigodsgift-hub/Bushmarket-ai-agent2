import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CooperativeMergeGroup(Base):
    """
    Dedicated ownership container for merged procurements.
    Replaces 'first cooperative owns merge' design.
    """

    __tablename__ = "cooperative_merge_groups"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    proposal_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("cooperative_merge_proposals.id"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )