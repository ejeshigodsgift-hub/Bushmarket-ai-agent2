from decimal import Decimal
from datetime import datetime
from typing import List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative_membership_procurement_allocation import (
    CooperativeMembershipProcurementAllocation
)

from app.db.models.cooperative_procurement_allocation import (
    CooperativeProcurementAllocation
)

from app.db.models.cooperative_contribution import CooperativeContribution


class CooperativeMembershipProcurementAllocationService:

    # =====================================================
    # CREATE MEMBER-LEVEL ALLOCATIONS (CORE LOGIC)
    # =====================================================
    async def create_member_allocations(
        self,
        db: AsyncSession,
        procurement_allocation: CooperativeProcurementAllocation,
    ) -> List[CooperativeMembershipProcurementAllocation]:

        # STEP 1: GET ALL CONTRIBUTIONS FOR THIS COOPERATIVE
        stmt = select(CooperativeContribution).where(
            CooperativeContribution.cooperative_id == procurement_allocation.cooperative_id,
            CooperativeContribution.status == "completed"
        )

        result = await db.execute(stmt)
        contributions = result.scalars().all()

        if not contributions:
            raise ValueError("No contributions found")

        # STEP 2: GROUP BY MEMBERSHIP
        membership_totals: Dict[str, Decimal] = {}

        membership_map: Dict[str, Dict] = {}

        for c in contributions:
            membership_id = c.membership_id

            membership_totals[membership_id] = membership_totals.get(
                membership_id,
                Decimal("0")
            ) + Decimal(str(c.amount))

            membership_map[membership_id] = {
                "user_id": c.user_id
            }

        total_contributed = sum(membership_totals.values())

        if total_contributed == 0:
            raise ValueError("Invalid contribution total")

        allocations: List[CooperativeMembershipProcurementAllocation] = []

        # STEP 3: ALLOCATE BASED ON MEMBER CONTRIBUTION SHARE
        for membership_id, amount in membership_totals.items():

            share_ratio = amount / total_contributed

            allocated_quantity = int(
                Decimal(procurement_allocation.allocated_quantity) * share_ratio
            )

            allocated_value = Decimal(procurement_allocation.allocated_value) * share_ratio

            allocation = CooperativeMembershipProcurementAllocation(
                procurement_id=procurement_allocation.procurement_id,
                cooperative_id=procurement_allocation.cooperative_id,
                membership_id=membership_id,
                user_id=membership_map[membership_id]["user_id"],
                allocation_ratio=share_ratio,
                allocated_quantity=allocated_quantity,
                allocated_value=allocated_value,
                created_at=datetime.utcnow()
            )

            db.add(allocation)
            allocations.append(allocation)

        # =========================================
# ALLOCATION ROUNDING RECONCILIATION
# =========================================

        allocated_total = sum(
            a.allocated_quantity for a in    allocations
        )

        remaining =    procurement_allocation.allocated_quantity   - allocated_total

        if remaining > 0:
            allocations[0].allocated_quantity +=  remaining

        await db.flush()

        return allocations

    # =====================================================
    # RUN FULL DISTRIBUTION FOR A PROCUREMENT
    # =====================================================
    async def distribute_for_procurement(
        self,
        db: AsyncSession,
        procurement_allocations: List[CooperativeProcurementAllocation],
    ):

        for allocation in procurement_allocations:
            await self.create_member_allocations(db, allocation)