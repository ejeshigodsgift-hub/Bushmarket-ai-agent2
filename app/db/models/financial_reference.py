# app/db/models/financial_reference.py

import uuid

from sqlalchemy import (
    String,
    DateTime,
    func,
    UniqueConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.base import Base


class FinancialReference(Base):

    __tablename__ = "financial_references"

    __table_args__ = (
        UniqueConstraint(
            "reference",
            name="uq_financial_reference"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )