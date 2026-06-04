import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Boolean,
    func,
    UniqueConstraint,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class CooperativeExtensionVote(Base):
    """
    Cooperative Expiry Extension Voting

    Members can vote once per extension round.

    Used for:
    - 48 hour extension
    - expiry recovery
    - partial procurement decision support
    """

    __tablename__ = "cooperative_extension_votes"

    __table_args__ = (
        UniqueConstraint(
            "cooperative_id",
            "user_id",
            "round_number",
            name="uq_coop_extension_vote"
        ),
        Index(
            "idx_extension_vote_cooperative",
            "cooperative_id"
        ),
        Index(
            "idx_extension_vote_user",
            "user_id"
        ),
        Index(
            "idx_extension_vote_round",
            "round_number"
        ),
    )

    # ====================================
    # PRIMARY KEY
    # ====================================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # ====================================
    # RELATIONSHIPS
    # ====================================
    cooperative_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "cooperatives.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # ====================================
    # VOTE
    # ====================================
    vote: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )
    """
    True  = extend cooperative
    False = proceed to partial procurement
    """

    # ====================================
    # EXTENSION ROUND
    # ====================================
    round_number: Mapped[int] = mapped_column(
        default=1,
        nullable=False
    )

    # ====================================
    # AUDIT
    # ====================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # ====================================
    # RELATIONSHIPS
    # ====================================
    cooperative = relationship(
        "Cooperative",
        lazy="selectin"
    )

    user = relationship(
        "User",
        lazy="selectin"
    )