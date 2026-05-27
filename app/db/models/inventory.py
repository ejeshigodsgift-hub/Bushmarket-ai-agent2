import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class Inventory(Base):

    __tablename__ = "inventories"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    product_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_products.id"),
        nullable=False,
        index=True
    )

    market_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_locations.id"),
        nullable=False,
        index=True
    )

    assigned_agent_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("market_agents.id"),
        nullable=False,
        index=True
    )

    measurement_unit_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("measurement_units.id"),
        nullable=False
    )

    available_stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    reserved_stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    sold_stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    damaged_stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="active"
    )
    # active
    # low_stock
    # out_of_stock
    # disabled

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    transactions = relationship(
        "InventoryTransaction",
        back_populates="inventory"
    )