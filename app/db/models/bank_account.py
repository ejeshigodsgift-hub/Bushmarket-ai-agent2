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
    mapped_column
)

from app.db.base import Base


class BankAccount(Base):

    __tablename__ = "bank_accounts"

    __table_args__ = (
        Index("idx_bank_account_user", "user_id"),
        Index("idx_bank_account_number", "account_number"),
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

    bank_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    account_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    account_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )