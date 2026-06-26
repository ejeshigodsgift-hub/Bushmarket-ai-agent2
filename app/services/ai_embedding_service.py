from sqlalchemy import select, desc

from app.db.models.ai_message import AIMessage
from app.db.models.ai_conversation import AIConversation


class AIEmbeddingService:

    async def embed_text(
        self,
        text: str
    ):
        """
        Placeholder until OpenAI embeddings
        are enabled.
        """
        return None

    async def find_similar_messages(
        self,
        db,
        user_id: str,
        query: str,
        limit: int = 10
    ):
        """
        Temporary fallback:
        return recent messages.
        """

        stmt = (
            select(AIMessage)
            .join(AIConversation)
            .where(
                AIConversation.user_id == user_id
            )
            .order_by(
                desc(AIMessage.created_at)
            )
            .limit(limit)
        )

        result = await db.execute(stmt)

        return result.scalars().all()


ai_embedding_service = AIEmbeddingService()