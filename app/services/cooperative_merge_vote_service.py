from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_merge_proposal import (
    CooperativeMergeProposal
)
from app.db.models.cooperative_merge_proposal_cooperative import (
    CooperativeMergeProposalCooperative
)
from app.db.models.cooperative_membership import (
    CooperativeMembership
)
from app.db.models.cooperative_merge_vote import (
    CooperativeMergeVote
)

from app.services.outbox_service import outbox_service
from app.services.cooperative_state_service import (
    cooperative_state_service
)
from app.services.cooperative_merge_service import (
    cooperative_merge_service
)


class CooperativeMergeVotingService:

    async def cast_vote(
        self,
        db: AsyncSession,
        proposal_id: str,
        member_id: str,
        vote: bool
    ):

        stmt = select(CooperativeMergeProposal).where(
            CooperativeMergeProposal.id == proposal_id,
            CooperativeMergeProposal.status == "voting"
        )

        result = await db.execute(stmt)
        proposal = result.scalar_one_or_none()

        if not proposal:
            raise ValueError("Invalid or closed proposal")

        if datetime.now(timezone.utc) > proposal.expires_at:
            proposal.status = "expired"
            await db.commit()
            return "EXPIRED"

        vote_obj = CooperativeMergeVote(
            proposal_id=proposal_id,
            member_id=member_id,
            vote=vote
        )

        db.add(vote_obj)

        await outbox_service.queue_event(
            db,
            "cooperative.merge.vote.cast",
            {
                "proposal_id": proposal_id,
                "member_id": member_id,
                "vote": vote
            }
        )

        await db.commit()

        return await self.evaluate(
            db=db,
            proposal_id=proposal_id
        )

    async def evaluate(
        self,
        db: AsyncSession,
        proposal_id: str
    ):

        stmt_prop = select(
            CooperativeMergeProposal
        ).where(
            CooperativeMergeProposal.id == proposal_id
        )

        proposal = (
            await db.execute(stmt_prop)
        ).scalar_one()

        stmt_coops = select(
            CooperativeMergeProposalCooperative
        ).where(
            CooperativeMergeProposalCooperative.proposal_id
            == proposal_id
        )

        coop_links = (
            await db.execute(stmt_coops)
        ).scalars().all()

        coop_ids = [
            c.cooperative_id
            for c in coop_links
        ]

        stmt_members = select(
            CooperativeMembership
        ).where(
            CooperativeMembership.cooperative_id.in_(coop_ids),
            CooperativeMembership.status == "active"
        )

        members = (
            await db.execute(stmt_members)
        ).scalars().all()

        member_count = len(members)

        if member_count == 0:
            return "NO_MEMBERS"

        stmt_votes = select(
            CooperativeMergeVote
        ).where(
            CooperativeMergeVote.proposal_id
            == proposal_id
        )

        votes = (
            await db.execute(stmt_votes)
        ).scalars().all()

        approvals = sum(
            1
            for v in votes
            if v.vote
        )

        approval_rate = (
            approvals / member_count
        ) * 100

        if approval_rate >= proposal.approval_threshold:

            proposal.status = "approved"

            await outbox_service.queue_event(
                db,
                "cooperative.merge.approved",
                {
                    "proposal_id": proposal.id,
                    "approval_rate": approval_rate
                }
            )

            await db.commit()

            # =====================================
            # LOAD COOPERATIVES
            # =====================================

            cooperatives = []

            for link in coop_links:

                coop = await db.get(
                    Cooperative,
                    link.cooperative_id
                )

                if coop:
                    cooperatives.append(coop)

            # =====================================
            # EXECUTE MERGE
            # =====================================

            merged = await cooperative_merge_service.execute_merge(
                db=db,
                cooperatives=cooperatives
            )

            # =====================================
            # MARK PROPOSAL EXECUTED
            # =====================================

            proposal.status = "executed"
            proposal.executed_at = datetime.now(
                timezone.utc
            )

            await outbox_service.queue_event(
                db,
                "cooperative.merge.executed",
                {
                    "proposal_id": proposal.id,
                    "merged_procurement_id": merged.id
                }
            )

            await db.commit()

            return "EXECUTED"

        return "VOTING"