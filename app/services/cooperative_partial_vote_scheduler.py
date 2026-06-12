from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.cooperative_partial_procurement_proposal import (
    CooperativePartialProcurementProposal
)

from app.services.cooperative_partial_voting_service import (
    CooperativePartialVotingService
)


class CooperativePartialVoteScheduler:

    async def close_expired_votes(self, db: AsyncSession):

        now = datetime.now(timezone.utc)

        stmt = select(CooperativePartialProcurementProposal).where(
            CooperativePartialProcurementProposal.status == "voting",
            CooperativePartialProcurementProposal.expires_at <= now
        )

        proposals = (await db.execute(stmt)).scalars().all()

        for proposal in proposals:

            # =====================================
            # EXPIRE CHECK (ADDED LOGIC)
            # =====================================
            if proposal.expires_at <= now and proposal.status == "voting":
                proposal.status = "expired"
                continue

            # =====================================
            # NORMAL EVALUATION
            # =====================================
            await CooperativePartialVotingService().evaluate_votes(
                db,
                proposal
            )

        await db.commit()