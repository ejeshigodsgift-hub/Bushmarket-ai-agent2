import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
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


class InventoryTransaction(Base):

    __tablename__ = "inventory_transactions"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    inventory_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("inventories.id"),
        nullable=False,
        index=True
    )

    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    # stock_in
    # reserve
    # release
    # sold
    # damaged

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    metadata: Mapped[dict] = mapped_column(
        JSON,
        nullable=True
    )

    created_by: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    inventory = relationship(
        "Inventory",
        back_populates="transactions"
    )