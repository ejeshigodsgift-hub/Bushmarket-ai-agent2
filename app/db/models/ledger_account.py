import uuid

from sqlalchemy import (
    String,
    DateTime,
    Boolean,
    ForeignKey,
    func,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LedgerAccount(Base):
    """
    Chart of Accounts for BushMarket Financial Core
    """

    __tablename__ = "ledger_accounts"

    __table_args__ = (
        Index("idx_ledger_account_user", "user_id"),
        Index("idx_ledger_account_type", "account_type"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    cooperative_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("cooperatives.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    account_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    """
    wallet | escrow | platform | settlement | commission
    """

    currency: Mapped[str] = mapped_column(
        String(10),
        default="NGN",
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    entries = relationship(
        "LedgerEntry",
        back_populates="account",
        lazy="selectin"
    )