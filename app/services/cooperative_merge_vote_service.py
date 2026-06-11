from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.outbox_service import outbox_service
from app.services.cooperative_state_service import (
    cooperative_state_service
)

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership


# =========================================================
# MERGE PROPOSAL MODEL
# =========================================================
class CooperativeMergeProposal:
    def __init__(self, cooperative_ids: list[str]):
        self.id = f"merge_{datetime.utcnow().timestamp()}"
        self.cooperative_ids = cooperative_ids
        self.status = "voting"
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=48)
        self.approval_threshold = 100


# =========================================================
# MERGE VOTE MODEL
# =========================================================
class CooperativeMergeVote:
    def __init__(self, proposal_id: str, member_id: str, vote: bool):
        self.id = f"mv_{datetime.utcnow().timestamp()}"
        self.proposal_id = proposal_id
        self.member_id = member_id
        self.vote = vote
        self.created_at = datetime.utcnow()


# =========================================================
# MERGE VOTING SERVICE
# =========================================================
class CooperativeMergeVotingService:

    async def cast_vote(
        self,
        db: AsyncSession,
        proposal: CooperativeMergeProposal,
        member_id: str,
        vote: bool
    ):

        if proposal.status != "voting":
            raise ValueError("Proposal not in voting state")

        if datetime.utcnow() > proposal.expires_at:
            proposal.status = "expired"
            return "EXPIRED"

        vote_obj = CooperativeMergeVote(
            proposal_id=proposal.id,
            member_id=member_id,
            vote=vote
        )

        await outbox_service.queue_event(
            db,
            "cooperative.merge.vote.cast",
            {
                "proposal_id": proposal.id,
                "member_id": member_id,
                "vote": vote
            }
        )

        return vote_obj

    async def evaluate(
        self,
        db: AsyncSession,
        proposal: CooperativeMergeProposal
    ):

        member_count = 0

        for coop_id in proposal.cooperative_ids:

            stmt = select(CooperativeMembership).where(
                CooperativeMembership.cooperative_id == coop_id,
                CooperativeMembership.status == "active"
            )

            result = await db.execute(stmt)
            members = result.scalars().all()

            member_count += len(members)

        # Replace with real vote aggregation later
        approval_rate = 100

        if approval_rate >= proposal.approval_threshold:

            proposal.status = "approved"

            # =====================================
            # STATE ENGINE (CORRECTED)
            # =====================================
            for coop_id in proposal.cooperative_ids:

                coop = await db.get(
                    Cooperative,
                    coop_id
                )

                if coop:
                    await cooperative_state_service.transition(
                        db=db,
                        cooperative=coop,
                        new_state="procurement_pending",
                        reason="merge_vote_approved"
                    )

            await outbox_service.queue_event(
                db,
                "cooperative.merge.approved",
                {
                    "proposal_id": proposal.id,
                    "cooperative_ids": proposal.cooperative_ids
                }
            )

            await db.commit()

            return "APPROVED"

        return "VOTING"