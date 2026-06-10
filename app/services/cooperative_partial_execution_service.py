from sqlalchemy.orm import Session

from app.db.models.cooperative_partial_procurement_proposal import (
    CooperativePartialProcurementProposal
)
from app.db.models.market_product_listing import MarketProductListing

from app.services.cooperative_partial_procurement_service import (
    CooperativePartialProcurementService
)


class CooperativePartialExecutionService:

    def execute_from_proposal(
        self,
        db: Session,
        proposal_id: str,
        listing: MarketProductListing
    ):
        """
        Executes partial procurement ONLY after full approval.
        """

        proposal = db.get(
            CooperativePartialProcurementProposal,
            proposal_id
        )

        if not proposal:
            raise ValueError("Proposal not found")

        # =====================================
        # STATE VALIDATION (CRITICAL GUARD)
        # =====================================
        if proposal.status != "approved":
            raise ValueError(f"Proposal not approved: {proposal.status}")

        if proposal.status == "executed":
            raise ValueError("Proposal already executed")

        if proposal.status == "expired":
            raise ValueError("Proposal expired")

        # =====================================
        # EXECUTION ENGINE
        # =====================================
        service = CooperativePartialProcurementService()

        procurement = service.create_partial_procurement(
            db=db,
            cooperative_id=proposal.cooperative_id,
            listing=listing,
            requested_quantity=proposal.requested_quantity,
            available_quantity=proposal.available_quantity,
            member_count=0,  # can later be injected from membership service
            total_cost=proposal.total_cost
        )

        # =====================================
        # UPDATE PROPOSAL STATE
        # =====================================
        proposal.status = "executed"
        proposal.executed_at = datetime.utcnow()

        db.commit()
        db.refresh(procurement)

        return procurement