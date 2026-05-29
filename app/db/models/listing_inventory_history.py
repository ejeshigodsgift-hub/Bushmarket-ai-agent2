import uuid

from sqlalchemy import (
    Integer,
    DateTime,
    ForeignKey,
    func,
    Index,
    Text
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InventoryHistory(Base):
    __tablename__ = "inventory_histories"

    __table_args__ = (
        Index("idx_inventory_history_inventory", "inventory_id"),
        Index("idx_inventory_history_created", "created_at"),
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

    previous_available_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    new_available_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    previous_reserved_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    new_reserved_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    previous_sold_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    new_sold_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    change_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    changed_by: Mapped[uuid.UUID | None] = mapped_column(
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
        back_populates="histories",
        lazy="joined"
    )

    changer = relationship(
        "User",
        lazy="joined"
    )