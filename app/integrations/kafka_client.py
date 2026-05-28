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

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def publish(
        self,
        topic: str,
        event: dict
    ):

        await self.producer.send_and_wait(
            topic,
            event
        )

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


event_bus = KafkaEventBus()