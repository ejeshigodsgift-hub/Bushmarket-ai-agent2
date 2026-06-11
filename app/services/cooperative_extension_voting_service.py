# app/services/cooperative_extension_vote_service.py

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.cooperative_extension_vote import CooperativeExtensionVote
from app.db.models.cooperative_membership import CooperativeMembership

from app.services.outbox_service import outbox_service


class CooperativeExtensionVoteService:
    """
    Handles cooperative lifespan extension voting logic
    (100% approval rule engine)
    """

    # =====================================================
    # CAST VOTE
    # =====================================================
    async def cast_vote(
        self,
        db: AsyncSession,
        cooperative_id: str,
        user_id: str,
        membership_id: str,
        round_number: int,
        vote: bool
    ):

        # -------------------------------------
        # Prevent duplicate vote (unique rule enforced also in DB)
        # -------------------------------------
        stmt = select(CooperativeExtensionVote).where(
            CooperativeExtensionVote.cooperative_id == cooperative_id,
            CooperativeExtensionVote.user_id == user_id,
            CooperativeExtensionVote.round_number == round_number
        )

        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError("User already voted in this round")

        # -------------------------------------
        # Create vote
        # -------------------------------------
        vote_record = CooperativeExtensionVote(
            cooperative_id=cooperative_id,
            user_id=user_id,
            membership_id=membership_id,
            round_number=round_number,
            vote=vote
        )

        db.add(vote_record)
        await db.commit()

        return await self.evaluate_round(
            db=db,
            cooperative_id=cooperative_id,
            round_number=round_number
        )

    # =====================================================
    # EVALUATION ENGINE (100% RULE)
    # =====================================================
    async def evaluate_round(
        self,
        db: AsyncSession,
        cooperative_id: str,
        round_number: int
    ):

        # -------------------------------------
        # Get all votes in this round
        # -------------------------------------
        stmt_votes = select(CooperativeExtensionVote).where(
            CooperativeExtensionVote.cooperative_id == cooperative_id,
            CooperativeExtensionVote.round_number == round_number
        )

        votes_result = await db.execute(stmt_votes)
        votes = votes_result.scalars().all()

        approvals = sum(1 for v in votes if v.vote)

        # -------------------------------------
        # Get active members
        # -------------------------------------
        stmt_members = select(CooperativeMembership).where(
            CooperativeMembership.cooperative_id == cooperative_id,
            CooperativeMembership.status == "active"
        )

        members_result = await db.execute(stmt_members)
        members = members_result.scalars().all()

        total_members = len(members)

        if total_members == 0:
            return "NO_ACTIVE_MEMBERS"

        approval_rate = (approvals / total_members) * 100

        # -------------------------------------
        # DECISION ENGINE
        # -------------------------------------
        if approval_rate >= 100:

            await outbox_service.queue_event(
                db,
                "cooperative.extension.approved",
                {
                    "cooperative_id": cooperative_id,
                    "round_number": round_number
                }
            )

            await db.commit()
            return "APPROVED_100_PERCENT"

        if approval_rate < 50:

            await outbox_service.queue_event(
                db,
                "cooperative.extension.rejected",
                {
                    "cooperative_id": cooperative_id,
                    "round_number": round_number
                }
            )

            await db.commit()
            return "REJECTED"

        return "VOTING_IN_PROGRESS"