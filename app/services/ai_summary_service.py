# app/services/ai_summary_service.py

from datetime import datetime, timezone

from sqlalchemy import select

from app.db.models.ai_message import AIMessage
from app.db.models.ai_conversation_summary import (
    AIConversationSummary
)

from app.services.llm_service import llm_service


import logging

logger = logging.getLogger(__name__)




class AISummaryService:

    async def summarize_conversation(
        self,
        db,
        conversation_id: str
    ):

        summary_record = await db.scalar(
            select(AIConversationSummary)
            .where(
                AIConversationSummary.conversation_id
                == conversation_id
            )
        )

        # =====================================
        # INCREMENTAL LOAD
        # =====================================
        if (
            summary_record
            and summary_record.last_summarized_at
        ):

            stmt = (
                select(AIMessage)
                .where(
                    AIMessage.conversation_id
                    == conversation_id,
                    AIMessage.created_at
                    >   summary_record.last_summarized_at
                )
                .order_by(
                    AIMessage.created_at.asc()
                )
            )

        else:

            stmt = (
                select(AIMessage)
                .where(
                    AIMessage.conversation_id
                    == conversation_id
                )
                .order_by(
                    AIMessage.created_at.asc()
                )
            )

        result = await db.execute(stmt)

        messages = result.scalars().all()

        if not messages:
            return summary_record

        if len(messages) < 100 and not summary_record:
            return None

        # =====================================
        # EXISTING SUMMARY
        # =====================================
        existing_summary = (
            summary_record.summary_text
            if summary_record
            else ""
        )

        # =====================================
        # LLM SUMMARY
        # =====================================
        try:

            summary_text =   llm_service.summarize_conversation(
                existing_summary,
                [
                    {
                        "role": m.role,
                        "content": m.content
                    }
                    for m in messages
                ]
            )

        except Exception as e:


            await ai_observability_service.log_request(
                db=db,
                operation="conversation_summary",
            conversation_id=conversation_id,
                status="failed",
                error_message=str(e)
            )

            logger.exception(
                f"AI summary failed for     conversation "
                f"{conversation_id}"
            )

            return summary_record

        last_message = messages[-1]

        

        if not summary_record:

            summary_record = AIConversationSummary(
                conversation_id=conversation_id,
                message_count_summarized=0
            )

            db.add(summary_record)

        summary_record.summary_text = summary_text

        summary_record.message_count_summarized += len(messages)

        summary_record.last_message_id = last_message.id

        summary_record.last_summarized_at = (
            datetime.now(timezone.utc)
        )

        await db.flush()

        await ai_observability_service.log_request(
            db=db,
            operation="conversation_summary",
            conversation_id=conversation_id,
            status="success",
            metadata={
                "messages_processed":   len(messages)
            }
        )

        return summary_record


ai_summary_service = AISummaryService()