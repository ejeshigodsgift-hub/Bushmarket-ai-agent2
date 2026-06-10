from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.cooperative_procurement import CooperativeProcurement
from app.db.models.market_product_listing import MarketProductListing


class CooperativePartialProcurementService:

    def create_partial_procurement(
        self,
        db: Session,
        cooperative_id: str,
        listing: MarketProductListing,
        requested_quantity: int,
        available_quantity: int,
        member_count: int,
        total_cost: Decimal,
    ) -> CooperativeProcurement:

        if available_quantity <= 0:
            raise ValueError("No stock available for partial procurement")

        final_quantity = min(requested_quantity, available_quantity)

        # scaling logic for partial fulfillment
        fulfillment_ratio = Decimal(final_quantity) / Decimal(requested_quantity)

        adjusted_cost = total_cost * fulfillment_ratio

        procurement = CooperativeProcurement(
            cooperative_id=cooperative_id,
            procurement_type="partial",
            procurement_value=adjusted_cost,
            procurement_quantity=final_quantity,
            estimated_retail_value=listing.unit_price * final_quantity,
            cooperative_buying_value=adjusted_cost,
            estimated_savings=(listing.unit_price * final_quantity) - adjusted_cost,
            savings_percentage=(
                ((listing.unit_price * final_quantity) - adjusted_cost)
                / (listing.unit_price * final_quantity)
            ) * Decimal("100"),
            status="approved",
            approved_at=datetime.utcnow()
        )

        db.add(procurement)

        listing.inventory.available_stock -= final_quantity
        listing.inventory.reserved_stock += final_quantity

        db.commit()
        db.refresh(procurement)

        return procurement

    def finalize_partial_procurement(self, db: Session, procurement: CooperativeProcurement):
        procurement.status = "completed"
        procurement.completed_at = datetime.utcnow()
        db.commit()
        return procurement