from fastapi import HTTPException

from app.integrations.redis_client import redis_client


class RateLimitService:

    async def check_limit(
        self,
        key: str,
        limit: int = 5,
        ttl: int = 60
    ):

        current = await redis_client.client.incr(key)

        if current == 1:
            await redis_client.client.expire(
                key,
                ttl
            )

        if current > limit:
            raise HTTPException(
                status_code=429,
                detail="Too many attempts"
            )