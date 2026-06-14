import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    ForeignKey,
    Numeric,
    DateTime,
    Text,
    func,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class CooperativePartialProcurement(Base):
    """
    Member-level allocation record created after an
    approved partial procurement is executed.

    One record = one member allocation.
    """

    __tablename__ = "cooperative_partial_procurements"

    __table_args__ = (
        Index(
            "idx_partial_procurement_cooperative",
            "cooperative_id"
        ),
        Index(
            "idx_partial_procurement_member",
            "member_id"
        ),
        Index(
            "idx_partial_procurement_procurement",
            "procurement_id"
        ),
    )

    # =====================================
    # PRIMARY KEY
    # =====================================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =====================================
    # CORE RELATIONSHIPS
    # =====================================
    cooperative_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "cooperatives.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    proposal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "cooperative_partial_procurement_proposals.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    member_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================
    # PROCUREMENT LINKAGE
    # =====================================
    procurement_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey(
            "cooperative_procurements.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # =====================================
    # ALLOCATION DATA
    # =====================================
    allocated_quantity: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0
    )

    unit_price: Mapped[float | None] = mapped_column(
        Numeric(18, 2),
        nullable=True
    )

    total_value: Mapped[float | None] = mapped_column(
        Numeric(18, 2),
        nullable=True
    )

    # =====================================
    # STATUS
    # =====================================
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="allocated"
    )
    """
    allocated
    completed
    refunded
    failed
    """

    # =====================================
    # FAILURE HANDLING
    # =====================================
    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # =====================================
    # TIMESTAMPS
    # =====================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    allocated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # =====================================
    # ORM RELATIONSHIPS
    # =====================================
    cooperative = relationship(
        "Cooperative",
        lazy="selectin"
    )

    proposal = relationship(
        "CooperativePartialProcurementProposal",
        lazy="selectin"
    )

    procurement = relationship(
        "CooperativeProcurement",
        lazy="selectin"
    )

    member = relationship(
        "User",
        lazy="selectin"
    )