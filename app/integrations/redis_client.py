import redis
import json

from app.core.config import settings


class RedisClient:

    def __init__(self):

        self.client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )

    # =========================
    # KEY-VALUE STORE
    # =========================

    def set(self, key: str, value, ttl: int = None):

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        self.client.set(key, value, ex=ttl)

    def get(self, key: str):

        value = self.client.get(key)

        if not value:
            return None

        try:
            return json.loads(value)
        except:
            return value

    def delete(self, key: str):
        self.client.delete(key)

    def exists(self, key: str):
        return self.client.exists(key)

    # =========================
    # PUBSUB EVENTS (KAFKA COMPANION LAYER)
    # =========================

    def publish(self, channel: str, message):

        if isinstance(message, dict):
            message = json.dumps(message)

        self.client.publish(channel, message)

    def subscribe(self, channel: str):
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)
        return pubsub


redis_client = RedisClient()