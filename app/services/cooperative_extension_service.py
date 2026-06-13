from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership
from app.db.models.cooperative_extension_vote import CooperativeExtensionVote

from app.services.cooperative_state_service import cooperative_state_service
from app.services.outbox_service import outbox_service
from app.services.cooperative_extension_vote_service import (
    CooperativeExtensionVoteService
)


class CooperativeExtensionService:

    # ====================================================
    # OPEN VOTE ROUND
    # ====================================================
    async def open_extension_vote(
        self,
        db: AsyncSession,
        cooperative: Cooperative
    ):

        await cooperative_state_service.transition(
            db=db,
            cooperative=cooperative,
            new_state="extension_vote",
            reason="expiry_window_open"
        )

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.extension.vote.opened",
            payload={
                "cooperative_id": cooperative.id
            }
        )

        return cooperative

    # ====================================================
    # CHECK TOTAL MEMBERS
    # ====================================================
    async def _get_total_members(
        self,
        db: AsyncSession,
        cooperative_id: str
    ) -> int:

        stmt = select(func.count(CooperativeMembership.id)).where(
            CooperativeMembership.cooperative_id == cooperative_id
        )

        return (await db.execute(stmt)).scalar() or 0

    # ====================================================
    # CHECK VOTES EXIST (TRUTH SOURCE)
    # ====================================================
    async def _votes_exist(
        self,
        db: AsyncSession,
        cooperative_id: str,
        round_number: int
    ) -> bool:

        stmt = select(func.count(CooperativeExtensionVote.id)).where(
            CooperativeExtensionVote.cooperative_id == cooperative_id,
            CooperativeExtensionVote.round_number == round_number
        )

        count = (await db.execute(stmt)).scalar() or 0

        return count > 0

    # ====================================================
    # APPROVE EXTENSION (80% RULE + REAL VALIDATION)
    # ====================================================
    async def approve_extension(
        self,
        db: AsyncSession,
        cooperative: Cooperative,
        extension_days: int,
        round_number: int
    ):

        # -------------------------------------
        # SAFETY CHECK: MEMBERS EXIST
        # -------------------------------------
        total_members = await self._get_total_members(
            db=db,
            cooperative_id=cooperative.id
        )

        if total_members == 0:
            raise ValueError("No members in cooperative")

        # -------------------------------------
        # SAFETY CHECK: VOTES EXIST
        # -------------------------------------
        if not await self._votes_exist(
            db=db,
            cooperative_id=cooperative.id,
            round_number=round_number
        ):
            raise ValueError("No extension votes recorded")

        # -------------------------------------
        # EVALUATION ENGINE (80% RULE)
        # -------------------------------------
        result = await CooperativeExtensionVoteService().evaluate_round(
            db=db,
            cooperative_id=cooperative.id,
            round_number=round_number
        )

        if result != "APPROVED_80_PERCENT":
            raise ValueError(
                f"Extension not approved: {result}"
            )

        # -------------------------------------
        # APPLY EXTENSION
        # -------------------------------------
        cooperative.ends_at = cooperative.ends_at + timedelta(days=extension_days)

        await cooperative_state_service.transition(
            db=db,
            cooperative=cooperative,
            new_state="active",
            reason="extension_approved"
        )

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.extension.approved",
            payload={
                "cooperative_id": cooperative.id,
                "extension_days": extension_days,
                "new_expiry": cooperative.ends_at.isoformat(),
                "round_number": round_number
            }
        )

        return cooperative

    # ====================================================
    # REJECT EXTENSION
    # ====================================================
    async def reject_extension(
        self,
        db: AsyncSession,
        cooperative: Cooperative,
        round_number: int
    ):

        await cooperative_state_service.transition(
            db=db,
            cooperative=cooperative,
            new_state="expired",
            reason="extension_rejected"
        )

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.extension.rejected",
            payload={
                "cooperative_id": cooperative.id,
                "round_number": round_number
            }
        )

        return cooperative


cooperative_extension_service = CooperativeExtensionService()