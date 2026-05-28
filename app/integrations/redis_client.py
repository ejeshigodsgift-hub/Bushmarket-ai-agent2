import json
import redis.asyncio as redis

from app.core.config import settings


class RedisClient:

    def __init__(self):

        self.client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )

    async def set(
        self,
        key: str,
        value,
        ttl: int = None
    ):

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        await self.client.set(
            key,
            value,
            ex=ttl
        )

    async def get(self, key: str):

        value = await self.client.get(key)

        if not value:
            return None

        try:
            return json.loads(value)

        except Exception:
            return value

    async def delete(self, key: str):
        await self.client.delete(key)

    async def exists(self, key: str):
        return await self.client.exists(key)


redis_client = RedisClient()