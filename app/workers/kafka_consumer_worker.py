import asyncio

from app.db.session import SessionLocal

from app.events.event_router import (event_router)

from app.integrations.kafka_client import (event_bus)

class KafkaConsumerWorker:

TOPICS = [
    "marketplace.order.created",
    "inventory_reserved",
    "escrow.deposit",
    "escrow.release",
]

GROUP_ID = "financial-core"

async def start(self):

    consumers = []

    for topic in self.TOPICS:

        consumer = await (
            event_bus.create_consumer(
                topic=topic,
                group_id=self.GROUP_ID
            )
        )

        consumers.append(
            (topic, consumer)
        )

    while True:

        for topic, consumer in consumers:

            async for message in consumer:

                async with SessionLocal() as db:

                    await event_router.route(
                        db=db,
                        topic=topic,
                        payload=message.value
                    )

                    await db.commit()

worker = KafkaConsumerWorker()