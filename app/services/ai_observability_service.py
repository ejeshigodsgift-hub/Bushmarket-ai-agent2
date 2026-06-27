from app.db.models.ai_request_log import (
    AIRequestLog
)


class AIObservabilityService:

    async def log_request(
        self,
        db,
        operation: str,
        status: str = "success",
        user_id: str | None = None,
        conversation_id: str | None = None,
        model_name: str | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        estimated_cost: float = 0,
        latency_ms: float = 0,
        error_message: str | None = None,
        metadata: dict | None = None
    ):

        db.add(
            AIRequestLog(
                user_id=user_id,
                conversation_id=conversation_id,
                operation=operation,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=estimated_cost,
                latency_ms=latency_ms,
                status=status,
                error_message=error_message,
                metadata_json=metadata
            )
        )

        await db.flush()


ai_observability_service = (
    AIObservabilityService()
)