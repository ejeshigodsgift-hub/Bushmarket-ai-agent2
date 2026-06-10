from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.cooperative_partial_procurement_proposal import (
    CooperativePartialProcurementProposal
)
from app.db.models.cooperative_partial_vote import CooperativePartialVote
from app.db.models.cooperative_membership import CooperativeMembership


class CooperativePartialVotingService:

    # =========================================
    # CREATE PROPOSAL
    # =========================================
    async def create_proposal(
        self,
        db: AsyncSession,
        cooperative_id: str,
        listing_id: str,
        requested_quantity: int,
        available_quantity: int,
        total_cost: float,
        voting_window_hours: int = 48
    ):

        proposal = CooperativePartialProcurementProposal(
            id=f"pp_{datetime.now(timezone.utc).timestamp()}",
            cooperative_id=cooperative_id,
            listing_id=listing_id,
            requested_quantity=requested_quantity,
            available_quantity=available_quantity,
            total_cost=total_cost,
            status="voting",
            approval_threshold=100,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=voting_window_hours)
        )

        db.add(proposal)
        await db.commit()
        await db.refresh(proposal)

        return proposal

    # =========================================
    # CAST VOTE
    # =========================================
    async def cast_vote(
        self,
        db: AsyncSession,
        proposal_id: str,
        member_id: str,
        vote: bool
    ):

        result = await db.execute(
            select(CooperativePartialProcurementProposal).where(
                CooperativePartialProcurementProposal.id == proposal_id
            )
        )
        proposal = result.scalar_one_or_none()

        if not proposal or proposal.status != "voting":
            raise ValueError("Voting not active")

        if proposal.expires_at < datetime.now(timezone.utc):
            proposal.status = "expired"
            await db.commit()
            raise ValueError("Voting expired")

        result = await db.execute(
            select(CooperativePartialVote).where(
                CooperativePartialVote.proposal_id == proposal_id,
                CooperativePartialVote.member_id == member_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError("Already voted")

        db.add(CooperativePartialVote(
            id=f"v_{datetime.now(timezone.utc).timestamp()}",
            proposal_id=proposal_id,
            member_id=member_id,
            vote=vote
        ))

        await db.commit()

        return await self.evaluate_votes(db, proposal)

    # =========================================
    # EVALUATION ENGINE (100% RULE)
    # =========================================
    async def evaluate_votes(self, db: AsyncSession, proposal):

        votes_result = await db.execute(
            select(CooperativePartialVote).where(
                CooperativePartialVote.proposal_id == proposal.id
            )
        )
        votes = votes_result.scalars().all()

        members_result = await db.execute(
            select(CooperativeMembership).where(
                CooperativeMembership.cooperative_id == proposal.cooperative_id,
                CooperativeMembership.status == "active"
            )
        )
        members = members_result.scalars().all()

        total_members = len(members)
        approvals = sum(1 for v in votes if v.vote)

        approval_rate = (approvals / total_members) * 100 if total_members else 0

        if approval_rate >= 100:
            proposal.status = "approved"
            await db.commit()
            return "APPROVED_100_PERCENT"

        if approval_rate < 50:
            proposal.status = "rejected"
            await db.commit()
            return "REJECTED"

        return "VOTING_IN_PROGRESS"