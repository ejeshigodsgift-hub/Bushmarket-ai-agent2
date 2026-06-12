from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership

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
            db,
            "cooperative.extension.vote.opened",
            {
                "cooperative_id": cooperative.id
            }
        )

        await db.commit()
        return cooperative

    # ====================================================
    # APPROVE EXTENSION (USES EVALUATION ENGINE)
    # ====================================================
    async def approve_extension(
        self,
        db: AsyncSession,
        cooperative: Cooperative,
        extension_days: int,
        round_number: int
    ):

        # -------------------------------------
        # RUN EVALUATION ENGINE (SINGLE SOURCE OF TRUTH)
        # -------------------------------------
        result = await CooperativeExtensionVoteService().evaluate_round(
            db=db,
            cooperative_id=cooperative.id,
            round_number=round_number
        )

        # -------------------------------------
        # STRICT ENFORCEMENT
        # -------------------------------------
        if result != "APPROVED_80_PERCENT":
            raise ValueError(
                f"Extension not approved. Result: {result}"
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
            db,
            "cooperative.extension.approved",
            {
                "cooperative_id": cooperative.id,
                "extension_days": extension_days,
                "new_expiry": cooperative.ends_at.isoformat(),
                "round_number": round_number
            }
        )

        await db.commit()
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
            db,
            "cooperative.extension.rejected",
            {
                "cooperative_id": cooperative.id,
                "round_number": round_number
            }
        )

        await db.commit()
        return cooperative


cooperative_extension_service = CooperativeExtensionService()