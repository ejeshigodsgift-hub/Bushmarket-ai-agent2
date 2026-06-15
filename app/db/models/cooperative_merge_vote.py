# app/db/models/cooperative_merge_vote.py

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class CooperativeMergeVote(Base):

    __tablename__ = "cooperative_merge_votes"

    __table_args__ = (
        UniqueConstraint(
            "proposal_id",
            "member_id",
            name="uq_merge_vote_member"
        ),
        Index(
            "idx_merge_vote_proposal",
            "proposal_id"
        ),
        Index(
            "idx_merge_vote_member",
            "member_id"
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
    # RELATIONSHIPS
    # =====================================

    proposal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "cooperative_merge_proposals.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    member_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "cooperative_memberships.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================
    # VOTE
    # =====================================

    vote: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )
    """
    True  = approve merge
    False = reject merge
    """

    # =====================================
    # TIMESTAMPS
    # =====================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # =====================================
    # RELATIONSHIPS
    # =====================================

    proposal = relationship(
        "CooperativeMergeProposal",
        lazy="selectin"
    )

    membership = relationship(
        "CooperativeMembership",
        lazy="selectin"
    )