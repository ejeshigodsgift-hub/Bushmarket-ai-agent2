from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_partial_procurement_proposal import (
    CooperativePartialProcurementProposal
)
from app.db.models.cooperative_partial_vote import CooperativePartialVote
from app.db.models.cooperative_membership import CooperativeMembership

from app.services.cooperative_state_service import (
    cooperative_state_service
)


class CooperativePartialVotingService:

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
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=voting_window_hours)
        )

        db.add(proposal)

        await db.commit()
        await db.refresh(proposal)

        return proposal

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

        db.add(
            CooperativePartialVote(
                id=f"v_{datetime.now(timezone.utc).timestamp()}",
                proposal_id=proposal_id,
                member_id=member_id,
                vote=vote
            )
        )

        await db.commit()
        
        await db.refresh(proposal)

        return await self.evaluate_votes(
            db,
            proposal
        )


    async def evaluate_votes(
        self,
        db: AsyncSession,
        proposal
    ):

        votes_result = await db.execute(
            select(CooperativePartialVote).where(
                CooperativePartialVote.proposal_id == proposal.id
            )
        )

        votes = votes_result.scalars().all()

        members_result = await db.execute(
            select(CooperativeMembership).where(
                CooperativeMembership.cooperative_id
                == proposal.cooperative_id,
                CooperativeMembership.status == "active"
            )
        )

        members = members_result.scalars().all()

        total_members = len(members)

        approvals = sum(
            1 for v in votes if v.vote
        )
     
        if total_members else 0
            return "VOTING_IN_PROGRESS"

        approval_rate = (
            (approvals / total_members) * 100
            
        )

        if approval_rate >= 80:

            proposal.status = "approved"

            # =====================================
            # STATE ENGINE (CORRECTED)
            # =====================================
            coop = await db.get(
                Cooperative,
                proposal.cooperative_id
            )

            if coop:
                await cooperative_state_service.transition(
                    db=db,
                    cooperative=coop,
                    new_state="procurement_pending",
                    reason="partial_procurement_approved"
                )

            await db.commit()

            return "APPROVED_100_PERCENT"

        if approval_rate < 50:

            proposal.status = "rejected"

            await db.commit()

            return "REJECTED"

        return "VOTING_IN_PROGRESS"