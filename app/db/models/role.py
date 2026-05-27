import uuid

from sqlalchemy import (
    String,
    ForeignKey,
    DateTime,
    func,
    UniqueConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class Role(Base):

    __tablename__ = "user_roles"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role",
            name="uq_user_role"
        ),
    )

    # =========================================
    # PRIMARY ID
    # =========================================

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================================
    # RELATION
    # =========================================

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # shopper | member | agent | admin
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # =========================================
    # RELATIONSHIP
    # =========================================

    user = relationship(
        "User",
        back_populates="roles"
    )