from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.market_product_listing import (
    MarketProductListing
)

from app.db.models.cooperative_partial_procurement_proposal import (
    CooperativePartialProcurementProposal
)

from app.db.models.cooperative_partial_procurement import (
    CooperativePartialProcurement
)

from app.db.models.cooperative_membership import (
    CooperativeMembership
)

from app.services.cooperative_partial_procurement_service import (
    CooperativePartialProcurementService
)


class CooperativePartialExecutionService:

    async def execute_from_proposal(
        self,
        db: AsyncSession,
        proposal_id: str,
        listing: MarketProductListing
    ):

        proposal = await db.get(
            CooperativePartialProcurementProposal,
            proposal_id
        )

        if not proposal:
            raise ValueError("Proposal not found")

        # -----------------------------
        # IDENTITY / IDEMPOTENCY GUARD
        # -----------------------------
        if proposal.status == "executed":
            return None

        if proposal.status == "expired":
            raise ValueError("Proposal expired")

        if proposal.status != "approved":
            raise ValueError(
                f"Proposal not approved: {proposal.status}"
            )

        procurement_service = CooperativePartialProcurementService()

        # -----------------------------
        # CREATE PROCUREMENT RECORD
        # -----------------------------
        procurement = await procurement_service.create_partial_procurement(
            db=db,
            cooperative_id=proposal.cooperative_id,
            listing=listing,
            requested_quantity=proposal.requested_quantity,
            available_quantity=proposal.available_quantity,
            member_count=0,
            total_cost=proposal.total_cost
        )

        coop = await db.get(
            Cooperative,
            proposal.cooperative_id
        )

        if (
            coop
            and coop.status ==   "procurement_pending"
        ):
            await   cooperative_state_service.transition(
                db=db,
                cooperative=coop,
                new_state="purchasing",
         reason="partial_procurement_executed"
            )

        # =========================================================
        # MEMBER ALLOCATION LOGIC (FIXED - WAS MISSING)
        # =========================================================

        members_result = await db.execute(
        select(CooperativeMembership).where(
        CooperativeMembership.cooperative_id == proposal.cooperative_id,
               CooperativeMembership.status == "active"
            )
        )

        members = members_result.scalars().all()

        if not members:
            raise ValueError("No active members for allocation")

        # distribute evenly across members
        per_member_quantity = (
            procurement.procurement_quantity /  len(members)
        )

        for member in members:

            allocation =   CooperativePartialProcurement(
         cooperative_id=proposal.cooperative_id,
                proposal_id=proposal.id,
                member_id=member.id,
                procurement_id=procurement.id,

         allocated_quantity=per_member_quantity,
              unit_price=listing.unit_price,
            total_value=per_member_quantity *  listing.unit_price,

                status="allocated",
          allocated_at=datetime.now(timezone.utc)
            )

            db.add(allocation)

# =====================================================
# CONTRIBUTION LINKING (NEW FIX ADDED HERE)
# =====================================================

        contrib_result = await db.execute(
     select(CooperativeContribution).where(
         CooperativeContribution.cooperative_id ==   proposal.cooperative_id,
                CooperativeContribution.status == "completed"
            )
        )

        contributions =   contrib_result.scalars().all()

        for c in contributions:
            c.procurement_id = procurement.id
          c.is_partial_procurement_related = True
        # -----------------------------
        # UPDATE PROPOSAL STATE
        # -----------------------------
        proposal.status = "executed"
        proposal.executed_at = datetime.now(timezone.utc)

        await db.commit()

        await db.refresh(procurement)

        return procurement