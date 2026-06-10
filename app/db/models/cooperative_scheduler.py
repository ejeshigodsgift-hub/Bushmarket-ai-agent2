from app.services.cooperative_expiry_service import CooperativeExpiryService


class CooperativeScheduler:

    def __init__(self):
        self.expiry = CooperativeExpiryService()

    async def run_hourly_tasks(self, db):

        await self.expiry.detect_expiring_cooperatives(db)

        await self.expiry.expire_cooperatives(db)