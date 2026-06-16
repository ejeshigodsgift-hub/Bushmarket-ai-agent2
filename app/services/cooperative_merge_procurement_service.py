from decimal import Decimal
from typing import List, Dict
from app.db.models.cooperative_merge_history import CooperativeMergeHistory
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative_procurement import CooperativeProcurement
from app.db.models.cooperative_contribution import CooperativeContribution

from app.db.models.cooperative_procurement_allocation import (
    CooperativeProcurementAllocation
)

from app.services.cooperative_membership_procurement_allocations_service import (
    CooperativeMembershipProcurementAllocationService
)


class CooperativeMergeProcurementService:

    def __init__(self):
        self.membership_allocation_service = (
            CooperativeMembershipProcurementAllocationService()
        )

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

        total_quantity = sum(
            p.procurement_quantity
            for p in procurements
        )

        total_value = sum(
            p.procurement_value
            for p in procurements
        )

        merged = CooperativeProcurement(
            cooperative_id=cooperative_id,
            procurement_type="merged",
            procurement_quantity=total_quantity,
            procurement_value=total_value,
            estimated_retail_value=sum(
                p.estimated_retail_value
                for p in procurements
            ),
            cooperative_buying_value=total_value,
            estimated_savings=sum(
                p.estimated_savings
                for p in procurements
            ),
            savings_percentage=Decimal("0"),
            status="approved",
            approved_at=datetime.utcnow()
        )

        db.add(merged)

        for procurement in procurements:
            procurement.status = "merged"

        await db.commit()
        await db.refresh(merged)

        return merged

    # =========================================
    # COOPERATIVE ALLOCATION ENGINE
    # =========================================
    async def create_allocations(
        self,
        db: AsyncSession,
        merged_procurement:   CooperativeProcurement,
        cooperative_ids: list[str]
    ) 
List[CooperativeProcurementAllocation]:

        stmt = select(
            CooperativeContribution
        ).where(
      CooperativeContribution.cooperative_id.in_(
        cooperative_ids
        ),
    CooperativeContribution.status ==  "completed"
    )

        result = await db.execute(stmt)

        contributions = result.scalars().all()

        if not contributions:
            raise ValueError(
                "No contributions found for allocation"
            )

        coop_totals: Dict[str, Decimal] = {}

        for contribution in contributions:

            coop_totals[
                contribution.cooperative_id
            ] = (
                coop_totals.get(
                    contribution.cooperative_id,
                    Decimal("0")
                )
                + Decimal(str(contribution.amount))
            )

        total_contributed = sum(
            coop_totals.values()
        )

        if total_contributed <= 0:
            raise ValueError(
                "Invalid contribution total"
            )

        allocations: List[
            CooperativeProcurementAllocation
        ] = []

        for cooperative_id, amount in coop_totals.items():

            share_ratio = (
                amount / total_contributed
            )

            allocated_quantity = int(
                Decimal(
                    merged_procurement.procurement_quantity
                ) * share_ratio
            )

            allocated_value = (
                Decimal(
                    str(
                        merged_procurement.procurement_value
                    )
                ) * share_ratio
            )

            allocation = (
                CooperativeProcurementAllocation(
                    procurement_id=merged_procurement.id,
                    cooperative_id=cooperative_id,
                    allocation_ratio=share_ratio,
                    allocated_quantity=allocated_quantity,
                    allocated_value=allocated_value,
                    created_at=datetime.utcnow()
                )
            )

            db.add(allocation)
            allocations.append(allocation)

        # =========================================
# ALLOCATION ROUNDING RECONCILIATION
# =========================================

        allocated_total = sum(
            a.allocated_quantity for a in   allocations
        )

        remaining =  merged_procurement.procurement_quantity -   allocated_total

        if remaining != 0 and allocations:
            allocations[0].allocated_quantity +=  remaining
            db.add(allocations[0])

        await db.commit()

        return allocations
    # =========================================
    # FINALIZE MERGE (ORCHESTRATOR)
    # =========================================
    async def finalize_merge(
        self,
        db: AsyncSession,
        merged: CooperativeProcurement,
        proposal_id: str,
        cooperative_ids: list[str]
    ) -> CooperativeProcurement:

        # ---------------------------------
        # STEP 1
        # Cooperative Allocations
        # ---------------------------------
        coop_allocations = (
            await self.create_allocations(
                db,
                merged,
                cooperative_ids
            )
        )

        # ---------------------------------
        # STEP 2
        # Membership Allocations
        # ---------------------------------
        await self.membership_allocation_service.distribute_for_procurement(
            db,
            coop_allocations
        )

        # ---------------------------------
        # STEP 3
        # Complete Merge
        # ---------------------------------
        merged.status = "completed"
        merged.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(merged)

        # ---------------------------------
        # STEP 4
        # FIXED HISTORY (Correction 6)
        # ---------------------------------
        history = CooperativeMergeHistory(
            proposal_id=proposal_id,   # ✅ FIXED (was merged.id)
            merged_procurement_id=merged.id,
            cooperative_ids=cooperative_ids,
            executed_at=datetime.now(timezone.utc)
        )

        db.add(history)
        await db.commit()

        return merged