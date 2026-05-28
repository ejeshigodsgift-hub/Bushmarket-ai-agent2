from sqlalchemy import select

from app.db.session import SessionLocal
from app.db.models.outbox_event import OutboxEvent

from app.integrations.kafka_client import event_bus


async def process_outbox_events():

    async with SessionLocal() as db:

        result = await db.execute(
            select(OutboxEvent).where(
                OutboxEvent.processed == False
            )
        )

        events = result.scalars().all()

        for event in events:

            try:

                await event_bus.publish(
                    event.topic,
                    event.payload
                )

                event.processed = True

            except Exception:

                event.retry_count += 1

        await db.commit()