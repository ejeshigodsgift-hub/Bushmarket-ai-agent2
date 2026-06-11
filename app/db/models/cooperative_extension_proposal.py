# app/db/models/cooperative_extension_proposal.py

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    func,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CooperativeExtensionProposal(Base):
    """
    Cooperative Extension Proposal

    Handles voting for extending cooperative lifespan.

    Flow:
    extension_vote → approved → active (extended)
                  → rejected → expired
    """

    __tablename__ = "cooperative_extension_proposals"

    __table_args__ = (
        Index("idx_extension_proposal_cooperative", "cooperative_id"),
        Index("idx_extension_proposal_status", "status"),
        Index("idx_extension_proposal_expires", "expires_at"),
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
    # RELATIONSHIPS
    # =====================================
    cooperative_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cooperatives.id", ondelete="CASCADE"),
        nullable=False
    )

    # =====================================
    # EXTENSION PARAMETERS
    # =====================================
    requested_extension_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    max_extension_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    min_extension_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # =====================================
    # VOTING CONFIG
    # =====================================
    approval_threshold: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False
    )

    total_votes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    approval_votes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    rejection_votes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # =====================================
    # STATUS
    # =====================================
    status: Mapped[str] = mapped_column(
        String(30),
        default="voting",
        nullable=False,
        index=True
    )
    """
    voting
    approved
    rejected
    expired
    executed
    """

    # =====================================
    # TIMING
    # =====================================
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # =====================================
    # METADATA
    # =====================================
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # =====================================
    # TIMESTAMPS
    # =====================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # =====================================
    # RELATIONSHIPS
    # =====================================
    cooperative = relationship(
        "Cooperative",
        lazy="selectin"
    )