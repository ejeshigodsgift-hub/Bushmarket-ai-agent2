import uuid
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AIShoppingSession(Base):
    __tablename__ = "ai_shopping_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id: Mapped[str] = mapped_column(String(36), index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), index=True)

    selected_listing_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    quantity: Mapped[int | None] = mapped_column()

    status: Mapped[str] = mapped_column(String(30), default="active")

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())