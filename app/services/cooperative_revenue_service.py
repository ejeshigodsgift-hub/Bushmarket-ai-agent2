# =========================================
# FILE: app/services/cooperative_revenue_service.py
# =========================================

from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.platform_settings import PlatformSettings
from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership


class CooperativeRevenueService:
    """
    Soft-coded revenue distribution engine
    (ADMIN CONTROLLED PERCENTAGES)
    """

    # =========================================
    # LOAD PLATFORM SETTINGS (SOFT-CODED)
    # =========================================
    async def _get_platform_settings(self, db: AsyncSession):

        stmt = select(PlatformSettings).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one()


    # =========================================
    # MAIN DISTRIBUTION ENGINE
    # =========================================
    async def distribute_cooperative_revenue(
        self,
        db: AsyncSession,
        cooperative: Cooperative,
        total_revenue: Decimal
    ):
        """
        Split cooperative revenue into:
        - platform
        - market
        - members pool
        """

        settings = await self._get_platform_settings(db)

        platform_fee = total_revenue * settings.platform_fee_percent
        market_fee = total_revenue * settings.market_fee_percent
        agent_fee = total_revenue * settings.agent_fee_percent

        # Remaining goes to cooperative members
        distributable_pool = (
            total_revenue
            - platform_fee
            - market_fee
            - agent_fee
        )

        # Load active members
        members_stmt = select(CooperativeMembership).where(
            CooperativeMembership.cooperative_id == cooperative.id,
            CooperativeMembership.status == "active"
        )

        members = (await db.execute(members_stmt)).scalars().all()

        if not members:
            raise Exception("No active cooperative members")

        per_member_share = distributable_pool / len(members)

        # Build result structure
        return {
            "cooperative_id": cooperative.id,
            "total_revenue": total_revenue,

            "platform_fee": platform_fee,
            "market_fee": market_fee,
            "agent_fee": agent_fee,

            "member_pool": distributable_pool,
            "per_member_share": per_member_share,

            "member_count": len(members)
        }