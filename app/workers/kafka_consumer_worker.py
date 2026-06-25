import asyncio

from app.db.session import SessionLocal

from app.events.event_router import (event_router)

from app.integrations.kafka_client import (event_bus)

class KafkaConsumerWorker:

TOPICS = [
    MARKETPLACE_ORDER_CREATED,
    PAYMENT_RECEIVED,
    PAYMENT_FAILED,
    ESCROW_DEPOSIT,
    ESCROW_RELEASE,
    ESCROW_REFUND,
    INVENTORY_RESERVED,
    NOTIFICATION_SMS_SEND,
    NOTIFICATION_EMAIL_SEND,
    NOTIFICATION_PUSH_SEND,
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