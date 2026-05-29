# app/events/event_dispatcher.py

from app.db.models.outbox_event import OutboxEvent

class EventDispatcher:
    def __init__(self, kafka_client):
        self.kafka = kafka_client

    async def dispatch(self, event: OutboxEvent):
        await self.kafka.publish(
            event.topic,
            event.payload
        )