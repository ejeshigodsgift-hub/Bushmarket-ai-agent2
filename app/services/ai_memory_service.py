from sqlalchemy import select, desc

from app.db.models.ai_message import AIMessage
from app.db.models.ai_conversation import AIConversation


class AIMemoryService:

    async def get_relevant_memory(
        self,
        db,
        user_id: str,
        query: str
    ):

        stmt = (
            select(AIMessage)
            .join(AIConversation)
            .where(
                AIConversation.user_id == user_id
            )
            .order_by(
                desc(AIMessage.created_at)
            )
            .limit(20)
        )

        result = await db.execute(stmt)
        messages = result.scalars().all()

        MAX_CHARS = 15000

        memory = []
        current_size = 0

        for msg in messages:

            if current_size >= MAX_CHARS:
                break

            memory.append(
                {
                    "role": msg.role,
                    "content": msg.content
                }
            )

            current_size += len(msg.content)

        return memory


ai_memory_service = AIMemoryService()