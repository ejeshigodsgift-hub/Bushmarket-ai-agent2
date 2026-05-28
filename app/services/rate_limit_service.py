from fastapi import HTTPException

from app.integrations.redis_client import redis_client


class RateLimitService:

    # =========================================
    # ATOMIC RATE LIMIT CHECK (ASYNC SAFE)
    # =========================================
    async def check_limit(
        self,
        key: str,
        limit: int = 5,
        ttl: int = 60
    ):

        client = redis_client.client

        # atomic increment
        current = await client.incr(key)

        # set expiry only on first hit
        if current == 1:
            await client.expire(key, ttl)

        # enforce limit
        if current > limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )

        return {
            "key": key,
            "count": current,
            "limit": limit
        }


rate_limit_service = RateLimitService()