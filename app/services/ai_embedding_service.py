class AIEmbeddingService:

    async def embed_text(
        self,
        text: str
    ):
        return None

    async def find_similar_messages(
        self,
        db,
        user_id: str,
        query: str,
        limit: int = 10
    ):
        return []


ai_embedding_service = AIEmbeddingService()