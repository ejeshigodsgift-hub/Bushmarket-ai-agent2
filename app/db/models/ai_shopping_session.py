import uuid
from sqlalchemy import String, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from sqlalchemy import (
    Index,
    CheckConstraint
)

class AIShoppingSession(Base):
    __tablename__ = "ai_shopping_sessions"


    __table_args__ = (

        Index(
            "idx_ai_session_user_conversation",
            "user_id",
            "conversation_id"
        ),

        Index(
            "idx_ai_session_status",
            "status"
        ),

        CheckConstraint(
            "quantity IS NULL OR quantity >= 0",
            name="ck_ai_session_quantity"
        ),
    )

    # =========================
    # PRIMARY KEY
    # =========================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # CONTEXT
    # =========================
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), index=True)

    selected_listing_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    quantity: Mapped[int | None] = mapped_column()

    # =========================
    # SHOPPING STATE MACHINE
    # =========================
    status: Mapped[str] = mapped_column(
        String(50),
        default="awaiting_market_selection"
    )
    # valid states:
    # - awaiting_market_selection
    # - awaiting_quantity
    # - awaiting_checkout_confirmation
    # - completed
    # - cancelled

    # =========================
    # EXTRA CONTEXT
    # =========================
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # =========================
    # TIMESTAMP
    # =========================
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )