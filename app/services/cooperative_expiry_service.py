from datetime import datetime, timedelta, timezone
from app.db.models.cooperative_extension_proposal import (
    CooperativeExtensionProposal
)

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

from app.services.cooperative_partial_service import (
    cooperative_partial_service
)

from app.services.cooperative_merge_service import (
    cooperative_merge_service
)


class CooperativeExpiryService:

    VOTE_WINDOW_HOURS = 48

    # =====================================================
    # DETECT COOPERATIVES ENTERING EXPIRY WINDOW
    # =====================================================
    async def  detect_expiring_cooperatives(
        self,
        db: AsyncSession
    ):

        now = datetime.now(timezone.utc)

        cutoff = now +  timedelta(hours=self.VOTE_WINDOW_HOURS)

        stmt = select(Cooperative).where(
            Cooperative.ends_at <= cutoff,
            Cooperative.status == "active"
        )

        result = await db.execute(stmt)
        cooperatives = result.scalars().all()

        opened = 0

        for coop in cooperatives:

            stmt =   select(CooperativeExtensionProposal).where(
            CooperativeExtensionProposal.cooperative_id == coop.id,
            CooperativeExtensionProposal.status == "voting"
            )

            existing = (
                await db.execute(stmt)
            ).scalar_one_or_none()

            if not existing:

                await cooperative_extension_service.open_extension_vote(
                    db=db,
                    cooperative=coop
                )

                opened += 1

        await db.commit()

        return opened

            
            
            # =================================================
            # 2. PARTIAL VOTE (NEW)
            # =================================================
            await cooperative_partial_service.open_partial_vote(
                db=db,
                cooperative=coop
            )

            # =================================================
            # 3. MERGE VOTE (NEW)
            # =================================================
            await cooperative_merge_service.open_merge_vote(
                db=db,
                cooperative=coop
            )

            # =================================================
            # EVENT NOTIFICATION (UI DASHBOARD TRIGGER)
            # =================================================
            await outbox_service.queue_event(
                db=db,
                topic="cooperative.expiry.window_open",
                payload={
                    "cooperative_id": coop.id,
                    "extension_vote": True,
                    "partial_vote": True,
                    "merge_vote": True
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
                ["active", "extension_vote"]
            )
        )

        result = await db.execute(stmt)
        cooperatives = result.scalars().all()

        expired = 0

        for coop in cooperatives:
        

            if coop.status == "extension_vote":
                continue

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