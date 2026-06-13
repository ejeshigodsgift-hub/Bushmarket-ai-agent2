from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Numeric,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base


class CooperativePartialProcurementProposal(Base):
    __tablename__ = "cooperative_partial_procurement_proposals"

    __table_args__ = (
        Index(
            "idx_partial_procurement_cooperative",
            "cooperative_id"
        ),
        Index(
            "idx_partial_procurement_status",
            "status"
        ),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    cooperative_id: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False
    )

    listing_id: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    requested_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    available_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    total_cost: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String,
        default="pending",
        nullable=False
    )
    """
    pending
    voting
    approved
    rejected
    expired
    executed
    """

    approval_threshold: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )