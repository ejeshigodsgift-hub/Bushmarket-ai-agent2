from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_product_listing import (
    MarketProductListing
)

from app.db.models.cooperative_partial_procurement_proposal import (
    CooperativePartialProcurementProposal
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
            raise ValueError(
                "Proposal not found"
            )

        # idempotency protection
        if proposal.status == "executed":
            return None

        if proposal.status == "expired":
            raise ValueError(
                "Proposal expired"
            )

        if proposal.status != "approved":
            raise ValueError(
                f"Proposal not approved: {proposal.status}"
            )

        procurement_service = (
            CooperativePartialProcurementService()
        )

        procurement = (
            await procurement_service.create_partial_procurement(
                db=db,
                cooperative_id=proposal.cooperative_id,
                listing=listing,
                requested_quantity=proposal.requested_quantity,
                available_quantity=proposal.available_quantity,
                member_count=0,
                total_cost=proposal.total_cost
            )
        )

        proposal.status = "executed"
        proposal.executed_at = datetime.now(
            timezone.utc
        )

        await db.commit()

        await db.refresh(procurement)

        return procurement