from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative
from app.services.outbox_service import outbox_service
from app.services.cooperative_state_service import (
    cooperative_state_service
)


class CooperativeExpiryService:

    VOTE_WINDOW_HOURS = 48

    async def detect_expiring_cooperatives(
        self,
        db: AsyncSession
    ):

        now = datetime.now(timezone.utc)

        cutoff = now + timedelta(
            hours=self.VOTE_WINDOW_HOURS
        )

        stmt = select(Cooperative).where(
            Cooperative.ends_at <= cutoff,
            Cooperative.status == "active"
        )

        result = await db.execute(stmt)
        cooperatives = result.scalars().all()

        for coop in cooperatives:
            await outbox_service.queue_event(
                db,
                "cooperative.expiry.window_open",
                {
                    "cooperative_id": coop.id
                }
            )

        await db.commit()

        return len(cooperatives)

    async def expire_cooperatives(
        self,
        db: AsyncSession
    ):

        now = datetime.now(timezone.utc)

        stmt = select(Cooperative).where(
            Cooperative.ends_at <= now,
            Cooperative.status == "active"
        )

        result = await db.execute(stmt)
        cooperatives = result.scalars().all()

        for coop in cooperatives:

            await cooperative_state_service.transition(
                db=db,
                cooperative=coop,
                new_state="expired",
                reason="lifespan_expired"
            )

            await outbox_service.queue_event(
                db,
                "cooperative.expired",
                {
                    "cooperative_id": coop.id
                }
            )

        await db.commit()

        return len(cooperatives)