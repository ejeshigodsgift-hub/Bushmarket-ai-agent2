import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    JSON,
    DateTime,
    ForeignKey,
    func,
    CheckConstraint,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentFieldReport(Base):

    __tablename__ = "agent_field_reports"

    __table_args__ = (
        CheckConstraint(
            "report_type IN ("
            "'supplier_report',"
            "'product_report',"
            "'market_price_report',"
            "'delivery_report'"
            ")",
            name="chk_agent_field_report_type"
        ),

        Index("idx_field_report_agent", "agent_id"),
        Index("idx_field_report_type", "report_type"),
        Index("idx_field_report_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    agent_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    cooperative_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    report_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )

    images: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )

    title: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    report_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    location: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )