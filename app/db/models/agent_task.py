import uuid

from datetime import datetime
from app.db.base import Base

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)


from sqlalchemy import (
    String,
    JSON,
    DateTime,
    ForeignKey,
    func,
    CheckConstraint
)

class AgentTask(Base):

    __tablename__ = "agent_tasks"

    __table_args__ = (
        CheckConstraint(
            """
            task_type IN (
                'product_sourcing',
                'supplier_verification',
                'market_price_check',
                'inventory_check',
                'live_market_stream',
                'listing_creation',
                'delivery_check',
                'supplier_contact'
            )
            """,
            name="chk_agent_task_type"
        ),
    )

    # existing fields remain unchanged

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    agent_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id",   ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    admin_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    cooperative_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    task_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String,
        default="assigned",
        nullable=False,
        index=True
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    retry_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )