from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_product_listing import (
    MarketProductListing
)

from app.db.models.cooperative_partial_procurement_proposal import (
    CooperativePartialProcurementProposal
)

from app.services.cooperative_partial_execution_service import (
    CooperativePartialExecutionService
)


class CooperativePartialVoteApprovedConsumer:

    async def handle(
        self,
        db: AsyncSession,
        payload: dict
    ):

        proposal_id = payload["proposal_id"]

        proposal = await db.get(
            CooperativePartialProcurementProposal,
            proposal_id
        )

        if not proposal:
            raise ValueError(
                f"Proposal not found: {proposal_id}"
            )

        if proposal.status != "approved":
            return

        listing = await db.get(
            MarketProductListing,
            proposal.listing_id
        )

        if not listing:
            raise ValueError(
                f"Listing not found: {proposal.listing_id}"
            )

        await CooperativePartialExecutionService().execute_from_proposal(
            db=db,
            proposal_id=proposal.id,
            listing=listing
        )