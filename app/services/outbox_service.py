from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.outbox_event import OutboxEvent


class OutboxService:

    async def queue_event(
        self,
        db: AsyncSession,
        topic: str,
        payload: dict
    ):

        event = OutboxEvent(
            topic=topic,
            payload=payload
        )

        db.add(event)

        return event


outbox_service = OutboxService()