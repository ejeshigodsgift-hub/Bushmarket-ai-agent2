# =========================================
# FILE: app/integrations/kafka_client.py
# =========================================

import json

from aiokafka import (
    AIOKafkaProducer,
    AIOKafkaConsumer
)

from app.core.config import settings


class KafkaEventBus:

    def __init__(self):

        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            client_id=settings.KAFKA_CLIENT_ID,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )

    # =========================================
    # START PRODUCER
    # =========================================
    async def start(self):
        await self.producer.start()

    # =========================================
    # STOP PRODUCER
    # =========================================
    async def stop(self):
        await self.producer.stop()

    # =========================================
    # PUBLISH EVENT
    # =========================================
    async def publish(
        self,
        topic: str,
        event: dict
    ):
        await self.producer.send_and_wait(
            topic,
            event
        )

    # =========================================
    # CREATE CONSUMER (PRIMARY METHOD)
    # =========================================
    async def create_consumer(
        self,
        topic: str,
        group_id: str
    ):

        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(
                m.decode("utf-8")
            )
        )

        await consumer.start()

        return consumer

    # =========================================
    # BACKWARD COMPATIBILITY
    # =========================================
    async def consumer(
        self,
        topic: str,
        group_id: str
    ):
        return await self.create_consumer(
            topic=topic,
            group_id=group_id
        )


event_bus = KafkaEventBus()