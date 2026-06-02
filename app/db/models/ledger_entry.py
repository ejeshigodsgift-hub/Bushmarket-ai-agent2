import uuid

from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    func,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LedgerEntry(Base):
    """
    Double-entry accounting core
    """

    __tablename__ = "ledger_entries"

    __table_args__ = (
        Index("idx_ledger_entry_account", "account_id"),
        Index("idx_ledger_entry_reference", "reference"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ledger_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    entry_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )
    """
    debit | credit
    """

    amount: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    """
    order_id | cooperative_id | payment_ref | escrow_ref
    """

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    account = relationship(
        "LedgerAccount",
        back_populates="entries",
        lazy="selectin"
    )