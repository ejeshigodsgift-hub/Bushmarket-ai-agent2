# app/db/models/cooperative_merge_proposal.py

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    Boolean,
    func,
    Index
)



from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base


class CooperativeMergeProposal(Base):
    """
    Cooperative Merge Proposal

    Governs merge voting between cooperatives.

    Flow:

    voting
        ↓
    approved
        ↓
    executed

    OR

    voting
        ↓
    rejected

    OR

    voting
        ↓
    expired
    """

    __tablename__ = "cooperative_merge_proposals"

    __table_args__ = (
        Index(
            "idx_merge_proposal_status",
            "status"
        ),
        Index(
            "idx_merge_proposal_expires",
            "expires_at"
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
    # APPROVAL CONFIG
    # =====================================
    approval_threshold: Mapped[int] = mapped_column(
        Integer,
        default=70,
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
        nullable=False
    )
    """
    voting
    approved
    rejected
    expired
    executed
    """

    # =====================================
    # EXPIRY
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
    # OPTIONAL NOTES
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