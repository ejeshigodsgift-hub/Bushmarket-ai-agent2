from datetime import datetime, timezone

from sqlalchemy import (
    select,
    or_
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.api_key import APIKey
from app.core.security import hash_api_key
from sqlalchemy.orm import mapped_column

class APIKeyService:

    # =========================================
    # VALIDATE API KEY
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
                APIKey.is_active.is_(True),
                or_(
                    APIKey.expires_at.is_(None),
                    APIKey.expires_at > datetime.now(timezone.utc)
                )
            )
        )

        api_key = result.scalar_one_or_none()

        return api_key


api_key_service = APIKeyService()