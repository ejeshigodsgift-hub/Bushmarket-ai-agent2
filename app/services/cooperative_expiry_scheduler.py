from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cooperative_expiry_service import (
    cooperative_expiry_service
)


class CooperativeExpiryScheduler:

    # =====================================================
    # RUN EVERY 1 HOUR (CRON / BACKGROUND TASK)
    # =====================================================
    async def run(self, db: AsyncSession):

        # STEP 1: open 48h voting window
        await cooperative_expiry_service.detect_expiring_cooperatives(db)

        # STEP 2: expire overdue cooperatives
        await cooperative_expiry_service.expire_cooperatives(db)

        return {
            "status": "completed"
        }


cooperative_expiry_scheduler = CooperativeExpiryScheduler()