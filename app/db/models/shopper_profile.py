import uuid

from sqlalchemy import String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ShopperProfile(Base):

    __tablename__ = "shopper_profiles"

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # RELATION TO USER
    # =========================
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True
    )

    # =========================
    # OPTIONAL CONTACT UPGRADE
    # =========================
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)

    # =========================
    # SHOPPER CONTEXT
    # =========================
    location: Mapped[str | None] = mapped_column(String, nullable=True)

    preferred_categories: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )

    # =========================
    # TIMESTAMP
    # =========================
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    # =========================
    # RELATIONSHIP
    # =========================
    user = relationship(
        "User",
        backref="shopper_profile",
        lazy="selectin"
    )