# app/workers/outbox_worker.py

from datetime import datetime, timezone
from sqlalchemy import select

from app.db.models.outbox_event import OutboxEvent
from app.db.session import SessionLocal
from app.events.event_dispatcher import EventDispatcher
from app.integrations.kafka_client import event_bus


async def process_outbox_events():
    dispatcher = EventDispatcher(event_bus)

    async with SessionLocal() as db:
        result = await db.execute(
            select(OutboxEvent).where(
                OutboxEvent.processed == False
            ).limit(100)
        )

        events = result.scalars().all()

        for event in events:
            try:
                await dispatcher.dispatch(event)

                event.processed = True
                event.processed_at = datetime.now(timezone.utc)

            except Exception:
                event.retry_count += 1

        await db.commit()