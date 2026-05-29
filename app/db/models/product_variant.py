import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    func,
    Index,
    UniqueConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class ProductVariant(Base):

    __tablename__ = "product_variants"

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "variant_name",
            name="uq_product_variant_name"
        ),
        Index("idx_product_variant_product", "product_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("market_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    variant_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    sku: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        unique=True
    )

    price_adjustment: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    product = relationship(
        "Product",
        back_populates="variants",
        lazy="joined"
    )