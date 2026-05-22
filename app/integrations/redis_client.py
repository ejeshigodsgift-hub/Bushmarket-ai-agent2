import redis
from app.core.config import settings


class RedisClient:
    def __init__(self):
        self.client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )

    def set(self, key: str, value: str, ttl: int = None):
        self.client.set(key, value, ex=ttl)

    def get(self, key: str):
        return self.client.get(key)

    def publish(self, channel: str, message: str):
        self.client.publish(channel, message)


redis_client = RedisClient()