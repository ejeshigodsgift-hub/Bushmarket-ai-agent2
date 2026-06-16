from datetime import timedelta, datetime, timezone


from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership
from app.db.models.cooperative_extension_vote import CooperativeExtensionVote
from app.db.models.cooperative_extension_proposal import CooperativeExtensionProposal
from app.db.models.platform_settings import PlatformSettings

from app.services.cooperative_state_service import cooperative_state_service
from app.services.outbox_service import outbox_service
from app.services.cooperative_extension_vote_service import (
    CooperativeExtensionVoteService
)


class CooperativeExtensionService:

    # ====================================================
    # OPEN VOTE ROUND (SYSTEM CONTROLLED)
    # ====================================================
    async def open_extension_vote(
        self,
        db: AsyncSession,
        cooperative: Cooperative
    ):

        # ----------------------------------------------------
        # PLATFORM SETTINGS FETCH (ADMIN CONTROLLED RULES)
        # ----------------------------------------------------
        settings = await db.scalar(
            select(PlatformSettings).where(
                PlatformSettings.is_active == True

        if not settings:
            raise ValueError("Platform settings not configured")

        # ----------------------------------------------------
        # SYSTEM CONTROLLED EXTENSION VALUE
        # ----------------------------------------------------
        # No user input allowed.
        # Extension is derived from platform policy.
        extension_days = settings.max_extension_days  # safe default policy-bound value

        # ----------------------------------------------------
        # CREATE PROPOSAL
        # ----------------------------------------------------
        proposal = CooperativeExtensionProposal(
            cooperative_id=cooperative.id,
            requested_extension_days=extension_days,
            max_extension_days=extension_days,
            min_extension_days=extension_days,
            approval_threshold=80,
            status="voting",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48)
        )

        db.add(proposal)
        await db.flush()  # ensure proposal.id exists before events

        # ----------------------------------------------------
        # STATE TRANSITION
        # ----------------------------------------------------
        await cooperative_state_service.transition(
            db=db,
            cooperative=cooperative,
            new_state="extension_vote",
            reason="expiry_window_open"
        )

        # ----------------------------------------------------
        # OUTBOX EVENT
        # ----------------------------------------------------
        await outbox_service.queue_event(
            db=db,
            topic="cooperative.extension.vote.opened",
            payload={
                "cooperative_id": cooperative.id,
                "proposal_id": proposal.id,
                "extension_days": extension_days,
                "round_number": cooperative.current_extension_round
            }
        )

        await db.commit()
        await db.refresh(proposal)

        return proposal

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
    # CHECK VOTES EXIST
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
    # APPROVE EXTENSION (PROPOSAL BASED)
    # ====================================================
    async def approve_extension(
        self,
        db: AsyncSession,
        cooperative: Cooperative,
        proposal_id: str,
        round_number: int
    ):

        proposal = await db.get(CooperativeExtensionProposal, proposal_id)

        if not proposal:
            raise ValueError("Proposal not found")

        if proposal.status != "voting":
            raise ValueError(f"Invalid proposal state: {proposal.status}")

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------
        total_members = await self._get_total_members(
            db=db,
            cooperative_id=cooperative.id
        )

        if total_members == 0:
            raise ValueError("No members in cooperative")

        if not await self._votes_exist(
            db=db,
            cooperative_id=cooperative.id,
            round_number=round_number
        ):
            raise ValueError("No extension votes recorded")

        # ----------------------------------------------------
        # EVALUATION ENGINE
        # ----------------------------------------------------
        result = await CooperativeExtensionVoteService().evaluate_round(
            db=db,
            cooperative_id=cooperative.id,
            round_number=round_number
        )

        if result != "APPROVED_80_PERCENT":
            proposal.status = "rejected"
            proposal.updated_at = datetime.now(timezone.utc)
            await db.commit()
            raise ValueError(f"Extension not approved: {result}")

        # ----------------------------------------------------
        # APPLY EXTENSION (SYSTEM CONTROLLED)
        # ----------------------------------------------------
        cooperative.ends_at = cooperative.ends_at + timedelta(
            days=proposal.max_extension_days
        )

        proposal.status = "approved"
        proposal.approved_at = datetime.now(timezone.utc)

        # ----------------------------------------------------
        # STATE TRANSITION
        # ----------------------------------------------------
        await cooperative_state_service.transition(
            db=db,
            cooperative=cooperative,
            new_state="active",
            reason="extension_approved"
        )

        # ----------------------------------------------------
        # OUTBOX EVENT
        # ----------------------------------------------------
        await outbox_service.queue_event(
            db=db,
            topic="cooperative.extension.approved",
            payload={
                "cooperative_id": cooperative.id,
                "proposal_id": proposal.id,
                "extension_days": proposal.max_extension_days,
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
        proposal_id: str,
        round_number: int
    ):

        proposal = await db.get(CooperativeExtensionProposal, proposal_id)

        if not proposal:
            raise ValueError("Proposal not found")

        proposal.status = "rejected"
        proposal.updated_at = datetime.now(timezone.utc)

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
                "proposal_id": proposal.id,
                "round_number": round_number
            }
        )

        await db.commit()
        return cooperative


cooperative_extension_service = CooperativeExtensionService()