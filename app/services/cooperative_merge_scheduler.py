from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.cooperative_merge_proposal import CooperativeMergeProposal
from app.db.models.cooperative_merge_proposal_cooperative import (
    CooperativeMergeProposalCooperative
)

from app.services.cooperative_merge_vote_service import (
    CooperativeMergeVotingService
)

from app.services.outbox_service import outbox_service


class CooperativeMergeScheduler:
    """
    Handles:
    - Expired merge proposals
    - Auto evaluation of voting results
    """

    async def process_merge_proposals(self, db: AsyncSession):

        now = datetime.now(timezone.utc)

        # =========================================
        # 1. GET ACTIVE VOTING PROPOSALS
        # =========================================
        stmt = select(CooperativeMergeProposal).where(
            CooperativeMergeProposal.status == "voting"
        )

        result = await db.execute(stmt)
        proposals = result.scalars().all()

        for proposal in proposals:

            # =========================================
            # EXPIRED PROPOSAL HANDLING
            # =========================================
            if proposal.expires_at <= now:

                proposal.status = "expired"

                await outbox_service.queue_event(
                    db,
                    "cooperative.merge.expired",
                    {
                        "proposal_id": proposal.id
                    }
                )

                continue

            # =========================================
            # AUTO-EVALUATE ACTIVE PROPOSAL
            # =========================================
            await CooperativeMergeVotingService().evaluate(
                db=db,
                proposal_id=proposal.id
            )

        await db.commit()
        return len(proposals)


cooperative_merge_scheduler = CooperativeMergeScheduler()