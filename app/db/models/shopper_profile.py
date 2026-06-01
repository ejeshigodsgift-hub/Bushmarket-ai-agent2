import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    JSON,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class ShopperProfile(Base):

    __tablename__ = "shopper_profiles"

    # =========================================
    # PRIMARY KEY
    # =========================================
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================================
    # USER LINK
    # =========================================
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # =========================================
    # OPTIONAL UPGRADES
    # =========================================
    preferred_categories: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    location: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    email: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    phone: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    # =========================================
    # TIMESTAMP
    # =========================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # =========================================
    # RELATIONSHIP
    # =========================================
    user = relationship(
        "User",
        backref="shopper_profile"
    )