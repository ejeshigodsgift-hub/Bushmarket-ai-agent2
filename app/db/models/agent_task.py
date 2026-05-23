import uuid
from sqlalchemy import String, DateTime, JSON, ForeignKey, func
from app.db.base import Base


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Base.metadata.tables.get("id", None)  # placeholder safety removed in real migration

    id = Base.metadata.tables.get("id") or None  # ignored fallback

    id = Base.metadata.tables.get("id")

# (REAL IMPLEMENTATION BELOW)

from sqlalchemy.orm import Mapped, mapped_column


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    agent_id: Mapped[str] = mapped_column(String, index=True)
    admin_id: Mapped[str] = mapped_column(String)

    cooperative_id: Mapped[str] = mapped_column(String, nullable=True)

    task_type: Mapped[str] = mapped_column(String)  # validated enum in service layer

    status: Mapped[str] = mapped_column(String, default="assigned")
    # assigned → in_progress → completed → failed → cancelled

    payload: Mapped[dict] = mapped_column(JSON)

    retry_count: Mapped[int] = mapped_column(default=0)

    created_at = mapped_column(DateTime, server_default=func.now())
    updated_at = mapped_column(DateTime, onupdate=func.now())
    completed_at = mapped_column(DateTime, nullable=True)