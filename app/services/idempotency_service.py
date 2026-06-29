import hashlib
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.idempotency_key import IdempotencyKey


class IdempotencyService:
    """
    Prevents duplicate execution of financial operations
    (CRITICAL for payment webhooks + retries)
    """

    # =========================================
    # GENERATE KEY
    # =========================================
    def generate_key(self, reference: str, action: str) -> str:
        raw = f"{reference}|{action}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # =========================================
    # CHECK IF ALREADY PROCESSED
    # =========================================
    async def is_processed(
        self,
        db: AsyncSession,
        key: str
    ) -> bool:

        stmt = select(IdempotencyKey).where(
            IdempotencyKey.key == key
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None


    
    # =========================================
    # COMPATIBILITY HELPERS
    # =========================================

    async def exists(
        self,
        db: AsyncSession,
        key: str
    ) -> bool:
        return await self.is_processed(
            db=db,
            key=key
        )

    async def record(
        self,
        db: AsyncSession,
        key: str
    ):
        return await self.mark_processed(
            db=db,
            key=key,
            reference=key,
            action="generic"
        )

    # =========================================
    # MARK AS PROCESSED
    # =========================================
    async def mark_processed(
        self,
        db: AsyncSession,
        key: str,
        reference: str,
        action: str
    ):

        record = IdempotencyKey(
            key=key,
            reference=reference,
            action=action,
            created_at=datetime.now(timezone.utc)
        )

        db.add(record)
        await db.flush()

        return record


idempotency_service = IdempotencyService()