from decimal import Decimal
from datetime import datetime
from typing import List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative_procurement import CooperativeProcurement
from app.db.models.cooperative_contribution import CooperativeContribution

from app.db.models.cooperative_procurement_allocation import (
    CooperativeProcurementAllocation
)


class CooperativeMergeProcurementService:

    # =========================================
    # MERGE PROCUREMENTS (ASYNC)
    # =========================================
    async def merge_procurements(
        self,
        db: AsyncSession,
        cooperative_id: str,
        procurements: List[CooperativeProcurement],
    ) -> CooperativeProcurement:

        if not procurements:
            raise ValueError("No procurements to merge")

        total_quantity = sum(p.procurement_quantity for p in procurements)
        total_value = sum(p.procurement_value for p in procurements)

        merged = CooperativeProcurement(
            cooperative_id=cooperative_id,
            procurement_type="merged",
            procurement_quantity=total_quantity,
            procurement_value=total_value,
            estimated_retail_value=sum(p.estimated_retail_value for p in procurements),
            cooperative_buying_value=total_value,
            estimated_savings=sum(p.estimated_savings for p in procurements),
            savings_percentage=Decimal("0"),
            status="approved",
            approved_at=datetime.utcnow()
        )

        db.add(merged)

        for p in procurements:
            p.status = "merged"

        await db.commit()
        await db.refresh(merged)

        return merged

    # =========================================
    # ALLOCATION ENGINE (ASYNC FIX)
    # =========================================
    async def create_allocations(
        self,
        db: AsyncSession,
        merged_procurement: CooperativeProcurement,
    ) -> List[CooperativeProcurementAllocation]:

        # STEP 1: GET CONTRIBUTIONS (ASYNC)
        stmt = select(CooperativeContribution).where(
            CooperativeContribution.cooperative_id == merged_procurement.cooperative_id,
            CooperativeContribution.status == "completed"
        )

        result = await db.execute(stmt)
        contributions = result.scalars().all()

        if not contributions:
            raise ValueError("No contributions found for allocation")

        # STEP 2: GROUP BY COOPERATIVE
        coop_totals: Dict[str, Decimal] = {}

        for c in contributions:
            coop_totals[c.cooperative_id] = coop_totals.get(
                c.cooperative_id,
                Decimal("0")
            ) + Decimal(str(c.amount))

        total_contributed = sum(coop_totals.values())

        if total_contributed == 0:
            raise ValueError("Invalid contribution total")

        allocations: List[CooperativeProcurementAllocation] = []

        # STEP 3: PROPORTIONAL ALLOCATION
        for cooperative_id, amount in coop_totals.items():

            share_ratio = amount / total_contributed

            allocated_quantity = int(
                Decimal(merged_procurement.procurement_quantity) * share_ratio
            )

            allocated_value = Decimal(
                merged_procurement.procurement_value
            ) * share_ratio

            allocation = CooperativeProcurementAllocation(
                procurement_id=merged_procurement.id,
                cooperative_id=cooperative_id,
                allocation_ratio=share_ratio,
                allocated_quantity=allocated_quantity,
                allocated_value=allocated_value,
                created_at=datetime.utcnow()
            )

            db.add(allocation)
            allocations.append(allocation)

        await db.commit()

        return allocations

    # =========================================
    # FINALIZE MERGE (ASYNC)
    # =========================================
    async def finalize_merge(
        self,
        db: AsyncSession,
        merged: CooperativeProcurement
    ) -> CooperativeProcurement:

        # STEP 1: CREATE ALLOCATIONS
        await self.create_allocations(db, merged)

        # STEP 2: COMPLETE MERGE
        merged.status = "completed"
        merged.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(merged)

        return merged