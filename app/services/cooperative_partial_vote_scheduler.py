from datetime import datetime, timezone
from app.db.models.cooperative import Cooperative
from app.services.cooperative_partial_execution_service import (
    CooperativePartialExecutionService
)

from app.db.models.market_product_listing import (
    MarketProductListing
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import text

from app.db.models.cooperative_partial_procurement_proposal import (
    CooperativePartialProcurementProposal
)

from app.services.cooperative_partial_voting_service import (
    CooperativePartialVotingService
)

from app.services.cooperative_state_service import (
    cooperative_state_service
)

from app.services.outbox_service import outbox_service


class CooperativePartialVoteScheduler:

    # =====================================================
    # MAIN JOB
    # =====================================================
    async def close_expired_votes(self, db: AsyncSession):

        now = datetime.now(timezone.utc)

        # =====================================================
        # 1. DISTRIBUTED LOCK (PREVENT DOUBLE CRON EXECUTION)
        # =====================================================
        lock_key = "partial_vote_scheduler_lock"

        locked = await db.execute(
            text(f"""
                SELECT pg_try_advisory_lock(hashtext('{lock_key}'))
            """)
        )

        if not locked.scalar():
            # another worker is already running this job
            return

        try:
            # =====================================================
            # STEP 1: EXPIRE ONLY
            # =====================================================
            expire_stmt = select(CooperativePartialProcurementProposal).where(
                CooperativePartialProcurementProposal.status == "voting",
                CooperativePartialProcurementProposal.expires_at <= now
            )

            expired = (await db.execute(expire_stmt)).scalars().all()

            for proposal in expired:
                proposal.status = "expired"

                await outbox_service.queue_event(
                    db,
                    "cooperative.partial_vote.expired",
                    {
                        "proposal_id": proposal.id,
                        "cooperative_id": proposal.cooperative_id
                    }
                )

            await db.commit()

            # =====================================================
            # STEP 2: EVALUATE ACTIVE PROPOSALS
            # =====================================================
            eval_stmt = select(CooperativePartialProcurementProposal).where(
                CooperativePartialProcurementProposal.status == "voting"
            )

            active = (await db.execute(eval_stmt)).scalars().all()

            service = CooperativePartialVotingService()

            for proposal in active:

                try:
                    # =================================================
                    # RESULT HANDLING
                    # =================================================
                    result = await service.evaluate_votes(db, proposal)

                    if result == "APPROVED_80_PERCENT":

                        

    await outbox_service.queue_event(
        db,
        "cooperative.partial_vote.approved",
        {
            "proposal_id": proposal.id,
            "cooperative_id": proposal.cooperative_id
        }
    )

                    elif result == "REJECTED":
                        await outbox_service.queue_event(
                            db,
                            "cooperative.partial_vote.rejected",
                            {
                                "proposal_id": proposal.id,
                                "cooperative_id": proposal.cooperative_id
                            }
                        )

                    # VOTING_IN_PROGRESS → do nothing

                except Exception as e:
                    # =================================================
                    # ERROR ISOLATION PER PROPOSAL
                    # =================================================
                    await outbox_service.queue_event(
                        db,
                        "cooperative.partial_vote.failed",
                        {
                            "proposal_id": proposal.id,
                            "error": str(e)
                        }
                    )
                    continue

            await db.commit()

        finally:
            # =====================================================
            # RELEASE LOCK
            # =====================================================
            await db.execute(
                text(f"""
                    SELECT pg_advisory_unlock(hashtext('{lock_key}'))
                """)
            )
            await db.commit()