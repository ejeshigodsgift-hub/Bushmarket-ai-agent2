import uuid

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    DateTime,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class Product(Base):

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    category_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("product_categories.id"),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True
    )

    slug: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    image_url: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    ai_keywords: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    cooperative_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    category = relationship(
        "ProductCategory",
        back_populates="products"
    )

    variants = relationship(
        "ProductVariant",
        back_populates="product"
    )

    measurements = relationship(
        "ProductMeasurement",
        back_populates="product"
    )