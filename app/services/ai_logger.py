# app/services/ai_logger.py

from datetime import datetime
from sqlalchemy import select

from app.db.models.ai_conversation import AIConversation
from app.db.models.ai_message import AIMessage
from app.db.models.ai_shopping_session import AIShoppingSession


class AILogger:

    # =========================================
    # GET OR CREATE CONVERSATION (FIXED)
    # =========================================
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
        await db.flush()  # ensures ID is available

        return conversation

    # =========================================
    # LOG USER MESSAGE
    # =========================================
    async def log_user_message(self, db, user_id: str, message: str):

        conversation = await self.get_or_create_conversation(db, user_id)

        msg = AIMessage(
            conversation_id=conversation.id,
            role="user",
            content=message,
            created_at=datetime.utcnow()
        )

        db.add(msg)
        await db.commit()

        return conversation.id

    # =========================================
    # LOG ASSISTANT MESSAGE (FIXED - MISSING BEFORE)
    # =========================================
    async def log_assistant_message(self, db, conversation_id: str, message: str):

        msg = AIMessage(
            conversation_id=conversation_id,
            role="assistant",
            content=message,
            created_at=datetime.utcnow()
        )

        db.add(msg)
        await db.commit()

    # =========================================
    # LOG SYSTEM ACTIONS
    # =========================================
    async def log_system_action(self, db, user_id: str, conversation_id: str, action: str, data: dict):

        session = AIShoppingSession(
            user_id=user_id,
            conversation_id=conversation_id,
            selected_listing_id=data.get("listing_id"),
            quantity=data.get("quantity"),
            status=action
        )

        db.add(session)
        await db.commit()

        return session.id


ai_logger = AILogger()