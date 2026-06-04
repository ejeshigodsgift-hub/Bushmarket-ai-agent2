import uuid

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class Beneficiary(Base):

    __tablename__ = "beneficiaries"

    __table_args__ = (
        Index("idx_beneficiary_user", "user_id"),
        Index("idx_beneficiary_wallet", "wallet_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    wallet_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False
    )

    bank_account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bank_accounts.id", ondelete="CASCADE"),
        nullable=False
    )

    recipient_code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    gateway: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="paystack"
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    bank_account = relationship(
        "BankAccount",
        lazy="joined"
    )