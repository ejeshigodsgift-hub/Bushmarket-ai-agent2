import uuid
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.db.base import Base


class ProductCategory(Base):

    __tablename__ = "product_categories"

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # CORE FIELDS
    # =========================
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    slug: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
        index=True
    )

    description: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    image_url: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    # =========================
    # CATEGORY HIERARCHY (OPTIONAL)
    # =========================
    parent_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("product_categories.id"),
        nullable=True,
        index=True
    )

    # =========================
    # SORT ORDER
    # =========================
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True
    )

    # =========================
    # STATUS
    # =========================
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # =========================
    # TIMESTAMP
    # =========================
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    # =========================
    # RELATIONSHIPS
    # =========================

    # 🔥 Product alignment (1 → many)
    products = relationship(
        "Product",
        back_populates="category",
        lazy="selectin"
    )

    # 🔥 self-referencing hierarchy
    parent = relationship(
        "ProductCategory",
        remote_side=[id],
        backref="children",
        lazy="selectin"
    )