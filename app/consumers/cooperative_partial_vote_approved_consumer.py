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

from app.services.outbox_service import (
    outbox_service
)


class CooperativePartialVoteApprovedConsumer:

    async def handle(
        self,
        db: AsyncSession,
        payload: dict
    ):

        proposal_id = payload.get(
            "proposal_id"
        )

        if not proposal_id:
            raise ValueError(
                "proposal_id missing from payload"
            )

        proposal = await db.get(
            CooperativePartialProcurementProposal,
            proposal_id
        )

        if not proposal:
            raise ValueError(
                f"Proposal not found: {proposal_id}"
            )

        # =====================================
        # IDEMPOTENCY
        # =====================================
        if proposal.status == "executed":
            return

        if proposal.status != "approved":
            return

        listing = await db.get(
            MarketProductListing,
            proposal.listing_id
        )

        if not listing:

            await outbox_service.queue_event(
                db,
                "cooperative.partial_procurement.failed",
                {
                    "proposal_id": proposal.id,
                    "cooperative_id": proposal.cooperative_id,
                    "reason": "listing_not_found"
                }
            )

            await db.commit()

            raise ValueError(
                f"Listing not found: {proposal.listing_id}"
            )

        try:

            procurement = await (
                CooperativePartialExecutionService()
                .execute_from_proposal(
                    db=db,
                    proposal_id=proposal.id,
                    listing=listing
                )
            )

            await outbox_service.queue_event(
                db,
                "cooperative.partial_procurement.executed",
                {
                    "proposal_id": proposal.id,
                    "cooperative_id": proposal.cooperative_id,
                    "procurement_id": (
                        procurement.id
                        if procurement
                        else None
                    )
                }
            )

            await db.commit()

        except Exception as e:

            await outbox_service.queue_event(
                db,
                "cooperative.partial_procurement.failed",
                {
                    "proposal_id": proposal.id,
                    "cooperative_id": proposal.cooperative_id,
                    "error": str(e)
                }
            )

            await db.commit()

            raise