from datetime import datetime
import json

from app.db.models.ai_conversation import AIConversation
from app.db.models.ai_message import AIMessage
from app.db.models.ai_shopping_session import AIShoppingSession


class AILogger:

    async def log_user_message(self, db, user_id: str, message: str):

        conversation = AIConversation(
            user_id=user_id
        )

        db.add(conversation)
        await db.flush()

        msg = AIMessage(
            conversation_id=conversation.id,
            role="user",
            content=message,
            created_at=datetime.utcnow()
        )

        db.add(msg)
        await db.commit()

        return conversation.id

    async def log_system_action(self, db, user_id: str, action: str, data: dict):

        session = AIShoppingSession(
            user_id=user_id,
            conversation_id=data.get("conversation_id", ""),
            selected_listing_id=data.get("listing_id"),
            quantity=data.get("quantity"),
            status=action
        )

        db.add(session)
        await db.commit()

        return session.id


ai_logger = AILogger()