import uuid
from sqlalchemy import String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CooperativeMessage(Base):

    __tablename__ = "cooperative_messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    cooperative_id: Mapped[str] = mapped_column(String(36), ForeignKey("cooperatives.id"))
    sender_id: Mapped[str] = mapped_column(String(36))
    message: Mapped[str] = mapped_column(Text)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )