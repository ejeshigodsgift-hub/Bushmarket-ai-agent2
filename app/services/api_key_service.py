from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.api_key import APIKey
from app.core.security import hash_api_key


class APIKeyService:

    # =========================================
    # VALIDATE API KEY (ASYNC SAFE VERSION)
    # =========================================
    async def validate_api_key(
        self,
        db: AsyncSession,
        raw_key: str
    ):

        hashed = hash_api_key(raw_key)

        result = await db.execute(
            select(APIKey).where(
                APIKey.key_hash == hashed,
                APIKey.is_active == True
            )
        )

        api_key = result.scalar_one_or_none()

        return api_key


api_key_service = APIKeyService()