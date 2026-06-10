import uuid
from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CooperativeDelivery(Base):

    __tablename__ = "cooperative_deliveries"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    cooperative_id: Mapped[str] = mapped_column(String(36))
    user_id: Mapped[str] = mapped_column(String(36))

    status: Mapped[str] = mapped_column(String(30), default="pending")

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )