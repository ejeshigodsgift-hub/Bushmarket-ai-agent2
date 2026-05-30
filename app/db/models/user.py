import uuid

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class User(Base):

    __tablename__ = "users"

    # =========================================
    # PRIMARY ID
    # =========================================

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================================
    # BASIC INFO
    # =========================================

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        unique=True,
        nullable=True
    )

    # =========================================
    # SECURITY
    # =========================================

    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # =========================================
    # TIMESTAMPS
    # =========================================

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # =========================================
    # RELATIONSHIPS
    # =========================================

    roles = relationship(
        "Role",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    
    listing_activities = relationship(
        "ListingAgentActivity",
        back_populates="agent"
    )