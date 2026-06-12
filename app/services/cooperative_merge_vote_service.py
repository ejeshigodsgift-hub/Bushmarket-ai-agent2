from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.outbox_service import outbox_service
from app.services.cooperative_state_service import cooperative_state_service

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership
from app.db.models.cooperative_merge_vote import CooperativeMergeVote


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

        # 70% approval rule
        self.approval_threshold = 70


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

        db.add(vote_obj)

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

    # =========================================================
    # EVALUATION ENGINE (70% MEMBERSHIP RULE)
    # =========================================================
    async def evaluate(
        self,
        db: AsyncSession,
        proposal: CooperativeMergeProposal
    ):

        # -------------------------------------------------
        # COUNT TOTAL ACTIVE MEMBERS ACROSS COOPERATIVES
        # -------------------------------------------------
        stmt_members = select(CooperativeMembership).where(
            CooperativeMembership.cooperative_id.in_(
                proposal.cooperative_ids
            ),
            CooperativeMembership.status == "active"
        )

        result = await db.execute(stmt_members)
        members = result.scalars().all()

        member_count = len(members)

        if member_count == 0:
            return "NO_MEMBERS"

        # -------------------------------------------------
        # FETCH VOTES FOR THIS PROPOSAL
        # -------------------------------------------------
        stmt_votes = select(CooperativeMergeVote).where(
            CooperativeMergeVote.proposal_id == proposal.id
        )

        vote_result = await db.execute(stmt_votes)
        votes = vote_result.scalars().all()

        total_votes = len(votes)

        approvals = sum(
            1 for v in votes if v.vote is True
        )

        # -------------------------------------------------
        # APPROVAL RATE CALCULATION
        # -------------------------------------------------
        approval_rate = (
            approvals / member_count
        ) * 100

        # =================================================
        # DECISION RULE: 70% MEMBERSHIP APPROVAL
        # =================================================
        if approval_rate >= 70:

            proposal.status = "approved"

            for coop_id in proposal.cooperative_ids:

                coop = await db.get(Cooperative, coop_id)

                if coop:
                    await cooperative_state_service.transition(
                        db=db,
                        cooperative=coop,
                        new_state="procurement_pending",
                        reason="merge_vote_approved_70_percent"
                    )

            await outbox_service.queue_event(
                db,
                "cooperative.merge.approved",
                {
                    "proposal_id": proposal.id,
                    "cooperative_ids": proposal.cooperative_ids,
                    "approval_rate": approval_rate
                }
            )

            await db.commit()
            return "APPROVED"

        # =================================================
        # NOT ENOUGH APPROVAL
        # =================================================
        return "VOTING"