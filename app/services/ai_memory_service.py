from sqlalchemy import select, desc

from app.db.models.ai_message import AIMessage
from app.db.models.ai_conversation import AIConversation
from app.db.models.ai_conversation_summary import (
    AIConversationSummary
)


class AIMemoryService:

    async def get_relevant_memory(
        self,
        db,
        user_id: str,
        query: str
    ):

        # =====================================
        # LOAD LATEST SUMMARY
        # =====================================
        summary = await db.scalar(
            select(AIConversationSummary)
            .join(AIConversation)
            .where(
                AIConversation.user_id == user_id
            )
            .order_by(
                AIConversationSummary.updated_at.desc()
            )
            .limit(1)
        )

        memory = []

        if summary and summary.summary_text:

            memory.append(
                {
                    "role": "system",
                    "content": summary.summary_text
                }
            )

        # =====================================
        # LOAD RECENT MESSAGES
        # =====================================
        stmt = (
            select(AIMessage)
            .join(AIConversation)
            .where(
                AIConversation.user_id == user_id
            )
            .order_by(
                desc(AIMessage.created_at)
            )
            .limit(30)
        )

        result = await db.execute(stmt)

        messages = result.scalars().all()

        # oldest -> newest
        messages.reverse()

        # =====================================
        # TOKEN / SIZE PROTECTION
        # =====================================
        MAX_CHARS = 15000

        current_size = sum(
            len(item["content"])
            for item in memory
        )

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