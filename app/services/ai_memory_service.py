class AIMemoryService:

    async def get_relevant_memory(self, db, user_id, query):
        # later upgrade: vector DB search
        return []


ai_memory_service = AIMemoryService()