# app/repositories/outbox_repository.py

from app.db.models.outbox_event import OutboxEvent

class OutboxRepository:

    async def add_event(self, uow, topic: str, payload: dict):
        event = OutboxEvent(
            topic=topic,
            payload=payload
        )

        await uow.add(event)
        return event