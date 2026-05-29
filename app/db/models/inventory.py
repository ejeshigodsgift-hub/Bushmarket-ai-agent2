import uuid

from sqlalchemy import (
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    Index,
    CheckConstraint,
    UniqueConstraint
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Inventory(Base):
    __tablename__ = "inventories"

    __table_args__ = (
        UniqueConstraint(
            "listing_id",
            name="uq_inventory_listing"
        ),
        Index("idx_inventory_listing", "listing_id"),
        Index("idx_inventory_active", "is_active"),
        CheckConstraint(
            "available_stock >= 0",
            name="ck_inventory_available_stock"
        ),
        CheckConstraint(
            "reserved_stock >= 0",
            name="ck_inventory_reserved_stock"
        ),
        CheckConstraint(
            "sold_stock >= 0",
            name="ck_inventory_sold_stock"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_product_listings.id", ondelete="CASCADE"),
        nullable=False
    )

    available_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    reserved_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    sold_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    last_restocked_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    listing = relationship(
        "MarketProductListing",
        back_populates="inventory",
        lazy="joined"
    )

    transactions = relationship(
        "InventoryTransaction",
        back_populates="inventory",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    histories = relationship(
        "InventoryHistory",
        back_populates="inventory",
        lazy="selectin",
        cascade="all, delete-orphan"
    )