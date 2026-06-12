import uuid
from datetime import datetime

from sqlalchemy import (
    String,
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


class CooperativeMergeProposalCooperative(Base):
    """
    Junction table linking a merge proposal
    to multiple cooperatives.

    One proposal -> many cooperatives
    One cooperative -> many merge proposals
    """

    __tablename__ = "cooperative_merge_proposal_cooperatives"

    __table_args__ = (
        UniqueConstraint(
            "proposal_id",
            "cooperative_id",
            name="uq_merge_proposal_cooperative"
        ),
        Index(
            "idx_merge_prop_coop_proposal",
            "proposal_id"
        ),
        Index(
            "idx_merge_prop_coop_cooperative",
            "cooperative_id"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    proposal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "cooperative_merge_proposals.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    cooperative_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "cooperatives.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    proposal = relationship(
        "CooperativeMergeProposal",
        lazy="selectin"
    )

    cooperative = relationship(
        "Cooperative",
        lazy="selectin"
    )