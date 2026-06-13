from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative

from app.services.outbox_service import outbox_service
from app.services.cooperative_state_service import (
    cooperative_state_service
)
from app.services.cooperative_extension_service import (
    cooperative_extension_service
)


class CooperativeExpiryService:

    VOTE_WINDOW_HOURS = 48

    # =====================================================
    # DETECT COOPERATIVES ENTERING EXPIRY WINDOW
    # =====================================================
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

        opened = 0

        for coop in cooperatives:

            # ----------------------------------------
            # OPEN EXTENSION VOTING AUTOMATICALLY
            # ----------------------------------------
            await cooperative_extension_service.open_extension_vote(
                db=db,
                cooperative=coop
            )

            await outbox_service.queue_event(
                db=db,
                topic="cooperative.expiry.window_open",
                payload={
                    "cooperative_id": coop.id
                }
            )

            opened += 1

        await db.commit()

        return opened

    # =====================================================
    # EXPIRE COOPERATIVES
    # =====================================================
    async def expire_cooperatives(
        self,
        db: AsyncSession
    ):

        now = datetime.now(timezone.utc)

        stmt = select(Cooperative).where(
            Cooperative.ends_at <= now,
            Cooperative.status.in_(
                [
                    "active",
                    "extension_vote"
                ]
            )
        )

        result = await db.execute(stmt)

        cooperatives = result.scalars().all()

        expired = 0

        for coop in cooperatives:

            await cooperative_state_service.transition(
                db=db,
                cooperative=coop,
                new_state="expired",
                reason="lifespan_expired"
            )

            await outbox_service.queue_event(
                db=db,
                topic="cooperative.expired",
                payload={
                    "cooperative_id": coop.id
                }
            )

            expired += 1

        await db.commit()

        return expired


cooperative_expiry_service = CooperativeExpiryService()