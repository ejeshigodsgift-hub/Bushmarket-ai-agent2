from decimal import Decimal
from datetime import datetime
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.cooperative_procurement import CooperativeProcurement
from app.db.models.market_product_listing import MarketProductListing
from app.db.models.inventory import Inventory


class CooperativeFullProcurementService:

  Async def create_full_procurement(
        self,
        db: AsyncSession,
        cooperative_id: str,
        listing: MarketProductListing,
        quantity: int,
        total_cost: Decimal,
    ) -> CooperativeProcurement:

        inventory: Inventory = listing.inventory

        if inventory.available_stock < quantity:
            raise ValueError("Insufficient stock for full procurement")

        procurement = CooperativeProcurement(
            cooperative_id=cooperative_id,
            procurement_type="full",
            procurement_value=total_cost,
            procurement_quantity=quantity,
            estimated_retail_value=listing.unit_price * quantity,
            cooperative_buying_value=total_cost,
            estimated_savings=(listing.unit_price * quantity) - total_cost,
            savings_percentage=(
                ((listing.unit_price * quantity) - total_cost)
                / (listing.unit_price * quantity)
            ) * Decimal("100"),
            status="approved",
            approved_at=datetime.utcnow()
        )

        db.add(procurement)

        # Reserve stock immediately
        inventory.available_stock -= quantity
        inventory.reserved_stock += quantity

        await db.commit()
        await db.refresh(procurement)

        return procurement

  Async def complete_procurement(self, db: AsyncSession, procurement: CooperativeProcurement):
        procurement.status = "completed"
        procurement.completed_at = datetime.utcnow()

        await db.commit()
        await return procurement