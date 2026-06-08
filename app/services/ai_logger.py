# app/services/ai_logger.py

from datetime import datetime
from sqlalchemy import select

from app.db.models.ai_conversation import AIConversation
from app.db.models.ai_message import AIMessage
from app.db.models.ai_shopping_session import AIShoppingSession


class AILogger:

    # =====================================================
    # CONVERSATION
    # =====================================================
    async def get_or_create_conversation(self, db, user_id: str):

        stmt = (
            select(AIConversation)
            .where(AIConversation.user_id == user_id)
            .order_by(AIConversation.created_at.desc())
            .limit(1)
        )

        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation:
            return conversation

        conversation = AIConversation(user_id=user_id)
        db.add(conversation)
        await db.flush()

        return conversation

    # =====================================================
    # UNIFIED MESSAGE LOGGER (UPDATED FIELD)
    # =====================================================
    async def log_message(
        self,
        db,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None
    ):

        msg = AIMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata or {},   # ✅ UPDATED HERE
            created_at=datetime.utcnow()
        )

        db.add(msg)
        return msg

    # =====================================================
    # BACKWARD COMPATIBILITY HELPERS
    # (NO LOGIC CHANGE, ONLY FIELD NAME)
    # =====================================================
    async def log_user_message(self, db, user_id: str, message: str, metadata: dict | None = None):

        conversation = await self.get_or_create_conversation(db, user_id)

        await self.log_message(
            db=db,
            conversation_id=conversation.id,
            role="user",
            content=message,
            metadata=metadata
        )

        return conversation.id

    async def log_assistant_message(self, db, conversation_id: str, message: str, metadata: dict | None = None):

        await self.log_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=message,
            metadata=metadata
        )

    # =====================================================
    # SYSTEM / SHOPPING ACTIONS (UNCHANGED)
    # =====================================================
    async def log_system_action(
        self,
        db,
        user_id: str,
        conversation_id: str,
        action: str,
        data: dict,
        metadata: dict | None = None
    ):

        session = AIShoppingSession(
            user_id=user_id,
            conversation_id=conversation_id,
            selected_listing_id=data.get("listing_id"),
            quantity=data.get("quantity"),
            status=action,
            metadata=metadata or {}
        )

        db.add(session)
        return session

    # =====================================================
    # BEHAVIOR SIGNALS (UNCHANGED)
    # =====================================================
    async def log_behavior_signal(
        self,
        db,
        user_id: str,
        event: str,
        listing_id: str | None = None,
        session_id: str | None = None,
        metadata: dict | None = None
    ):

        session = AIShoppingSession(
            user_id=user_id,
            conversation_id=None,
            selected_listing_id=listing_id,
            quantity=1,
            status=event,
            metadata={
                "session_id": session_id,
                **(metadata or {})
            }
        )

        db.add(session)
        return session


ai_logger = AILogger()