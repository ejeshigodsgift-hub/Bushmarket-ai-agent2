from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.procurement_base_service import (
    ProcurementBaseService,
)

from app.db.models.cooperative_procurement import (
    CooperativeProcurement,
)
from app.db.models.market_product_listing import (
    MarketProductListing,
)
from app.db.models.inventory import Inventory


class CooperativeFullProcurementService(
    ProcurementBaseService
):

    async def create_full_procurement(
        self,
        db: AsyncSession,
        cooperative_id: str,
        listing: MarketProductListing,
        quantity: int,
        total_cost: Decimal,
    ) -> CooperativeProcurement:

        inventory: Inventory = listing.inventory

        if inventory.available_stock < quantity:
            raise ValueError(
                "Insufficient stock for full procurement"
            )

        savings = self.calculate_savings(
            unit_price=listing.unit_price,
            qty=quantity,
            cost=total_cost,
        )

        procurement = CooperativeProcurement(
            cooperative_id=cooperative_id,
            procurement_type="full",
            procurement_value=total_cost,
            procurement_quantity=quantity,
            estimated_retail_value=savings["retail"],
            cooperative_buying_value=total_cost,
            estimated_savings=savings["savings"],
            savings_percentage=savings["percent"],
            status="approved",
            approved_at=datetime.now(timezone.utc),
        )

        db.add(procurement)

        inventory.available_stock -= quantity
        inventory.reserved_stock += quantity

        await db.commit()
        await db.refresh(procurement)

        coop = await db.get(
            Cooperative,
            cooperative_id
        )

        if coop and coop.status ==    "procurement_pending":
            await   cooperative_state_service.transition(
                db=db,
                cooperative=coop,
                new_state="purchasing",
                reason="full_procurement_created"
    )

        return procurement

    async def complete_procurement(
        self,
        db: AsyncSession,
        procurement: CooperativeProcurement,
    ):

        procurement.status = "completed"
        procurement.completed_at = datetime.now(
            timezone.utc
        )

        await db.commit()

        return procurement