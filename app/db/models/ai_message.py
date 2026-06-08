import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text, func, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIMessage(Base):
    __tablename__ = "ai_messages"

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # CONVERSATION LINK
    # =========================
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ai_conversations.id"),
        index=True,
        nullable=False
    )

    # =========================
    # MESSAGE DATA
    # =========================
    role: Mapped[str] = mapped_column(String(20))  # user | assistant | system

    content: Mapped[str] = mapped_column(Text)

    metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    # =========================
    # TIMESTAMP
    # =========================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # =========================
    # RELATIONSHIP
    # =========================
    conversation = relationship(
        "AIConversation",
        back_populates="messages",
        lazy="selectin"
    )