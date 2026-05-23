from fastapi import HTTPException
from app.integrations.redis_client import redis_client


class RateLimitService:

    def check_limit(
        self,
        key: str,
        limit: int = 5,
        ttl: int = 60
    ):

        existing = redis_client.get(key)

        count = int(existing) if existing else 0

        if count >= limit:
            raise HTTPException(
                status_code=429,
                detail="Too many attempts"
            )

        redis_client.set(
            key,
            str(count + 1),
            ttl=ttl
        )