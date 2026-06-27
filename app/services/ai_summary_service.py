from sqlalchemy import select

from app.db.models.ai_message import AIMessage


class AISummaryService:

    async def summarize_conversation(
        self,
        db,
        conversation_id: str
    ):

        messages = await db.execute(
            select(AIMessage)
            .where(
                AIMessage.conversation_id == conversation_id
            )
            .order_by(AIMessage.created_at.asc())
        )

        messages = messages.scalars().all()

        if len(messages) < 100:
            return None

        summary_text = (
            f"Conversation summary: "
            f"{len(messages)} messages exchanged."
        )

        return {
            "conversation_id": conversation_id,
            "summary": summary_text
        }


ai_summary_service = AISummaryService()