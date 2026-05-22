from kafka import KafkaProducer, KafkaConsumer
from app.core.config import settings
import json


class KafkaEventBus:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            client_id=settings.KAFKA_CLIENT_ID,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    def publish(self, topic: str, event: dict):
        self.producer.send(topic, event)
        self.producer.flush()

    def consumer(self, topic: str, group_id: str):
        return KafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )


event_bus = KafkaEventBus()