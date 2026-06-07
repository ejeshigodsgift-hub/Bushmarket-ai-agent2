from sqlalchemy import select, desc
from app.db.models.ai_message import AIMessage
from app.db.models.ai_conversation import AIConversation


class AIMemoryService:

    async def get_relevant_memory(self, db, user_id: str, query: str):

        stmt = (
            select(AIMessage)
            .join(AIConversation)
            .where(AIConversation.user_id == user_id)
            .order_by(desc(AIMessage.created_at))
            .limit(10)
        )

        result = await db.execute(stmt)
        messages = result.scalars().all()

        return [
            {
                "role": m.role,
                "content": m.content
            }
            for m in messages
        ]


ai_memory_service = AIMemoryService()