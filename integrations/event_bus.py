class EventBus:

    def subscribe(self, event_type: str, handler):
        # placeholder for Kafka / Redis / RabbitMQ
        pass

    def publish(self, event_type: str, payload: dict):
        print(f"[EVENT] {event_type}: {payload}")


# EJESHI Cross check


import redis
import json


class EventBus:

    def __init__(self):
        self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)

    def publish(self, event_type: str, payload: dict):
        self.redis.publish(event_type, json.dumps(payload))