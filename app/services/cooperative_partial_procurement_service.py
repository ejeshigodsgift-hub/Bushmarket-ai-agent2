from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.services.procurement_base_service import ProcurementBaseService

from app.db.models.cooperative_procurement import (
    CooperativeProcurement,
)

from app.db.models.market_product_listing import (
    MarketProductListing,
)

from app.db.models.cooperative_contribution import (
    CooperativeContribution,
)


from fastapi import HTTPException

from app.db.models.cooperative_member import (
    CooperativeMember
)

class CooperativePartialProcurementService(
    ProcurementBaseService
):

    async def create_partial_procurement(
        self,
        db: AsyncSession,
        cooperative_id: str,
        listing: MarketProductListing,
        requested_quantity: int,
        available_quantity: int,
        member_count: int,
        total_cost: Decimal,
    ) -> CooperativeProcurement:

        # ==========================================
        # 1. VALIDATE STOCK
        # ==========================================
        if available_quantity <= 0:
            raise ValueError(
                "No stock available for partial procurement"
            )

        # ==========================================
        # 2. CALCULATE TOTAL MEMBER CONTRIBUTIONS
        # ==========================================
        contributions_result = await db.execute(
            select(
                func.coalesce(func.sum(CooperativeContribution.amount), 0)
            ).where(
                CooperativeContribution.cooperative_id == cooperative_id,
                CooperativeContribution.status == "completed"
            )
        )

        available_funds = contributions_result.scalar() or 0

        # Ensure Decimal safety
        available_funds = Decimal(str(available_funds))
        unit_price = Decimal(str(listing.unit_price or 0))

        if unit_price <= 0:
            raise ValueError("Invalid listing unit price")

        # ==========================================
        # 3. CALCULATE AFFORDABLE QUANTITY
        # ==========================================
        affordable_quantity = int(
            available_funds / unit_price
        )

        if affordable_quantity <= 0:
            raise ValueError(
                "Insufficient cooperative funds for procurement"
            )

        # ==========================================
        # 4. FINAL QUANTITY (CORE BUSHMARKET RULE)
        # ==========================================
        final_quantity = min(
            requested_quantity,
            available_quantity,
            affordable_quantity
        )

        if final_quantity <= 0:
            raise ValueError(
                "Final computed quantity is invalid"
            )

        # ==========================================
        # 5. FINANCIAL CALCULATIONS
        # ==========================================
        fulfillment_ratio = (
            Decimal(final_quantity)
            / Decimal(requested_quantity)
        )

        adjusted_cost = total_cost * fulfillment_ratio

        # ==========================================
        # 6. SAVINGS CALCULATION
        # ==========================================
        savings = self.calculate_savings(
            unit_price=listing.unit_price,
            qty=final_quantity,
            cost=adjusted_cost,
        )

        # ==========================================
        # 7. CREATE PROCUREMENT RECORD
        # ==========================================
        procurement = CooperativeProcurement(
            cooperative_id=cooperative_id,
            procurement_type="partial",
            procurement_value=adjusted_cost,
            procurement_quantity=final_quantity,
            estimated_retail_value=savings["retail"],
            cooperative_buying_value=adjusted_cost,
            estimated_savings=savings["savings"],
            savings_percentage=savings["percent"],
            status="approved",
            approved_at=datetime.now(timezone.utc),
        )

        db.add(procurement)

        # ==========================================
        # 8. UPDATE INVENTORY
        # ==========================================
        listing.inventory.available_stock -= final_quantity
        listing.inventory.reserved_stock += final_quantity

        # ==========================================
        # 9. COMMIT
        # ==========================================
        await db.commit()
        await db.refresh(procurement)

        return procurement

    async def finalize_partial_procurement(
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




    async def create_partial_order(
        self,
        db: AsyncSession,
        cooperative_id: str,
        listing_id: str,
        requested_quantity: int,
    ):

        listing = await db.get(
            MarketProductListing,
            listing_id
       )

        if not listing:
            raise HTTPException(
                404,
                "Listing not found"
            )

        available_quantity = (
            listing.inventory.available_stock
        )

        if available_quantity <= 0:
            raise HTTPException(
                400,
                "No stock available"
            )

        member_result = await db.execute(
            select(
            func.count(CooperativeMember.id)
            ).where(
            CooperativeMember.cooperative_id
                == cooperative_id
            )
        )

        member_count = (
            member_result.scalar() or 0
        )

        total_cost = (
            listing.unit_price
            * requested_quantity
        )

        return await self.create_partial_procurement(
            db=db,
            cooperative_id=cooperative_id,
            listing=listing,
        requested_quantity=requested_quantity,
        available_quantity=available_quantity,
            member_count=member_count,
            total_cost=total_cost
        )