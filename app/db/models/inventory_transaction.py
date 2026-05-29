import uuid

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    func,
    Index,
    CheckConstraint,
    Text
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    __table_args__ = (
        Index("idx_inventory_transaction_inventory", "inventory_id"),
        Index("idx_inventory_transaction_type", "transaction_type"),
        Index("idx_inventory_transaction_created", "created_at"),
        CheckConstraint(
            "quantity > 0",
            name="ck_inventory_transaction_quantity"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    inventory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventories.id", ondelete="CASCADE"),
        nullable=False
    )

    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )

    reference_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    inventory = relationship(
        "Inventory",
        back_populates="transactions",
        lazy="joined"
    )

    creator = relationship(
        "User",
        lazy="joined"
    )