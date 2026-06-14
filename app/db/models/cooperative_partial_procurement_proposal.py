import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Numeric,
    ForeignKey,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
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
        Index(
            "idx_partial_procurement_expires",
            "expires_at"
        ),
    )

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    # =========================
    # CORE REFERENCES (FIXED)
    # =========================
    cooperative_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("cooperatives.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    listing_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_product_listings.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # =========================
    # PROCUREMENT DATA
    # =========================
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

    # =========================
    # LIFECYCLE STATUS
    # =========================
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

    # =========================
    # VOTING RULES
    # =========================
    approval_threshold: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False
    )

    # =========================
    # TIMESTAMPS
    # =========================
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=datetime.datetime.utcnow,
        nullable=False
    )

    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    approved_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    rejected_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    executed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    # =========================
    # RELATIONSHIPS (OPTIONAL BUT RECOMMENDED)
    # =========================
    cooperative = relationship(
        "Cooperative",
        lazy="selectin"
    )

    listing = relationship(
        "MarketProductListing",
        lazy="selectin"
    )