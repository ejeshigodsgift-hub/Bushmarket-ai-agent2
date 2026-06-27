import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    Text,
    ForeignKey,
    func,
    Index
)

import logging



from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)


from app.db.base import Base


logger = logging.getLogger(__name__)

class AIConversationSummary(Base):
    __tablename__ = "ai_conversation_summaries"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "ai_conversations.id",
            ondelete="CASCADE"
        ),
        unique=True,
        index=True
    )

    summary_text: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    message_count_summarized: Mapped[int] = mapped_column(
        default=0
    )

    last_message_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True
    )

    last_summarized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
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

    conversation = relationship(
        "AIConversation",
        lazy="selectin"
    )

    __table_args__ = (
        Index(
            "idx_ai_summary_conversation",
            "conversation_id"
        ),
    )