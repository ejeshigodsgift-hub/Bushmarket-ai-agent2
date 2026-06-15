from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.market_product_listing import MarketProductListing
from app.db.models.cooperative import Cooperative

from app.db.models.cooperative_partial_procurement_proposal import (
    CooperativePartialProcurementProposal,
)

from app.db.models.cooperative_partial_procurement import (
    CooperativePartialProcurement,
)

from app.db.models.cooperative_membership import (
    CooperativeMembership,
)

from app.services.cooperative_partial_procurement_service import (
    CooperativePartialProcurementService,
)

from app.services.cooperative_state_service import (
    cooperative_state_service,
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

        if proposal.status == "executed":
            return None

        if proposal.status == "expired":
            raise ValueError("Proposal expired")

        if proposal.status != "approved":
            raise ValueError(f"Proposal not approved: {proposal.status}")

        procurement_service = CooperativePartialProcurementService()

        # =========================
        # CREATE PROCUREMENT
        # =========================
        procurement = await procurement_service.create_partial_procurement(
            db=db,
            cooperative_id=proposal.cooperative_id,
            listing=listing,
            requested_quantity=proposal.requested_quantity,
            available_quantity=proposal.available_quantity,
            member_count=0,
            total_cost=proposal.total_cost
        )

        # =========================
        # STATE TRANSITION
        # =========================
        coop = await db.get(Cooperative, proposal.cooperative_id)

        if coop and coop.status == "procurement_pending":
            await cooperative_state_service.transition(
                db=db,
                cooperative=coop,
                new_state="purchasing",
                reason="partial_procurement_executed"
            )

        # =========================
        # MEMBERS FETCH
        # =========================
        members_result = await db.execute(
            select(CooperativeMembership).where(
                CooperativeMembership.cooperative_id == proposal.cooperative_id,
                CooperativeMembership.status == "active"
            )
        )

        members = members_result.scalars().all()

        if not members:
            raise ValueError("No active members for allocation")

        member_count = len(members)
        total_qty = procurement.procurement_quantity

        # =========================
        # FLOOR + REMAINDER ALLOCATION
        # =========================
        base_qty = total_qty // member_count
        remainder = total_qty % member_count

        for i, member in enumerate(members):

            allocated_qty = base_qty + (1 if i < remainder else 0)

            allocation = CooperativePartialProcurement(
                cooperative_id=proposal.cooperative_id,
                proposal_id=proposal.id,
                member_id=member.id,
                procurement_id=procurement.id,
                allocated_quantity=allocated_qty,
                unit_price=listing.unit_price,
                total_value=allocated_qty * listing.unit_price,
                status="allocated",
                allocated_at=datetime.now(timezone.utc)
            )

            db.add(allocation)

        # =========================
        # CONTRIBUTION LINKING
        # =========================
        from app.db.models.cooperative_contribution import CooperativeContribution

        contrib_result = await db.execute(
            select(CooperativeContribution).where(
                CooperativeContribution.cooperative_id == proposal.cooperative_id,
                CooperativeContribution.status == "completed"
            )
        )

        contributions = contrib_result.scalars().all()

        for c in contributions:
            c.procurement_id = procurement.id
            c.is_partial_procurement_related = True

        # =========================
        # FINALIZE PROPOSAL
        # =========================
        proposal.status = "executed"
        proposal.executed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(procurement)

        return procurement