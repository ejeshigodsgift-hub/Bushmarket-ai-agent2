# =========================================
# FILE: app/db/models/agent_application.py
# =========================================

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    func
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class AgentApplication(Base):

    __tablename__ = "agent_applications"

    # =========================================
    # PRIMARY KEY
    # =========================================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # =========================================
    # APPLICANT USER
    # =========================================
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # =========================================
    # APPLICATION DETAILS
    # =========================================
    motivation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    experience: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # =========================================
    # APPLICATION STATUS
    # =========================================
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True
    )

    # pending
    # approved
    # rejected
    # suspended

    # =========================================
    # REVIEW METADATA
    # =========================================
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # =========================================
    # AUDIT / LIFECYCLE
    # =========================================
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

    # =========================================
    # RELATIONSHIPS
    # =========================================
    applicant = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="joined"
    )

    reviewer = relationship(
        "User",
        foreign_keys=[reviewed_by],
        lazy="joined"
    )

    # =========================================
    # TABLE CONSTRAINTS
    # =========================================
    __table_args__ = (

        # STRICT STATUS CONTROL
        CheckConstraint(
            """
            status IN (
                'pending',
                'approved',
                'rejected',
                'suspended'
            )
            """,
            name="chk_agent_application_status"
        ),

        # PREVENT MULTIPLE ACTIVE APPLICATIONS
        UniqueConstraint(
            "user_id",
            name="uq_agent_application_user"
        ),

        # PERFORMANCE INDEXES
        Index(
            "idx_agent_application_created_at",
            "created_at"
        ),

        Index(
            "idx_agent_application_reviewed_by",
            "reviewed_by"
        ),
    )