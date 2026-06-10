from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db.models.cooperative import Cooperative
from app.services.outbox_service import outbox_service


class CooperativeCheckoutService:

    async def trigger_checkout(self, db: AsyncSession, cooperative_id: str):

        coop = await db.get(Cooperative, cooperative_id)

        if not coop:
            raise HTTPException(404, "Cooperative not found")

        if coop.status != "funded":
            raise HTTPException(400, "Cooperative not funded")

        await outbox_service.queue_event(
            db,
            "cooperative.checkout.triggered",
            {
                "cooperative_id": cooperative_id,
                "product_ids": coop.product_ids,
                "total_amount": str(coop.target_amount)
            }
        )

        coop.status = "purchasing"

        await db.commit()

        return {"status": "checkout_started"}