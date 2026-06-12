from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal

from app.services.cooperative_extension_vote_service import (
    CooperativeExtensionVoteService
)

from app.services.cooperative_partial_voting_service import (
    CooperativePartialVotingService
)

# If you already have a scheduler abstraction, plug it here
from app.services.cooperative_partial_vote_scheduler import (
    cooperative_partial_vote_scheduler
)


class CooperativeJobs:
    """
    Background job runner for cooperative system.
    """

    def __init__(self):
        self.extension_vote_service = CooperativeExtensionVoteService()
        self.partial_vote_service = CooperativePartialVotingService()

    # =====================================================
    # RUN ALL JOBS (ENTRY POINT)
    # =====================================================
    async def run_all(self):
        async with AsyncSessionLocal() as db:
            await self.run_partial_vote_jobs(db)
            await self.run_extension_vote_jobs(db)

    # =====================================================
    # 10. PARTIAL VOTE SCHEDULER JOB
    # =====================================================
    async def run_partial_vote_jobs(self, db: AsyncSession):
        """
        Runs every 5–15 minutes via cron/system scheduler.
        Responsible for closing expired partial procurement votes.
        """

        await cooperative_partial_vote_scheduler.close_expired_votes(
            db=db
        )

        # Optional: you can also trigger evaluation sweep
        # (useful if votes are still pending evaluation)
        await self._evaluate_pending_partial_votes(db)

    async def _evaluate_pending_partial_votes(self, db:   AsyncSession):

        from app.db.models.cooperative_partial_procure ment_proposal import (
        CooperativePartialProcurementProposal
        )

        from sqlalchemy import select

        stmt = select(CooperativePartialProcurementProposal).where(
        CooperativePartialProcurementProposal.status == "voting"
        )

        result = await db.execute(stmt)
        proposals = result.scalars().all()

        for proposal in proposals:
            await self.partial_vote_service.evaluate_votes(
                db=db,
                proposal=proposal
            )
    # =====================================================
    # EXTENSION VOTE JOBS
    # =====================================================
    async def run_extension_vote_jobs(self, db: AsyncSession):
        """
        Handles expired extension voting rounds and evaluation.
        """

        # Example placeholder logic:
        # You should replace this with your real scheduler if exists
        await self._close_expired_extension_votes(db)

    async def _close_expired_extension_votes(self, db: AsyncSession):
        """
        Finds expired extension votes and triggers evaluation.
        """

        # If you already have a scheduler service, connect it here
        # Example:
        # await cooperative_extension_vote_scheduler.close_expired(db)

        pass