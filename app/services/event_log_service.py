# =========================================
# FILE: app/services/event_log_service.py
# =========================================

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.event_log import EventLog


class EventLogService:

    async def log_event(
        self,
        db: AsyncSession,
        event_name: str,
        event_category: str,
        topic: str,
        payload: dict | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        user_id: str | None = None,
        source_service: str | None = None,
        ip_address: str | None = None,
        message: str | None = None,
        status: str = "processed"
    ) -> EventLog:

        event = EventLog(
            event_name=event_name,
            event_category=event_category,
            topic=topic,
            source_service=source_service,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            ip_address=ip_address,
            payload=payload,
            message=message,
            status=status
        )

        db.add(event)

        await db.flush()

        return event


event_log_service = EventLogService()