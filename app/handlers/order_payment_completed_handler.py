FILE: app/handlers/order_payment_completed_handler.py

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.services.delivery_lifecycle_service import (
    delivery_lifecycle_service
)


class OrderPaymentCompletedHandler:

    async def handle(
        self,
        db: AsyncSession,
        payload: dict
    ):
        order = await db.get(
            Order,
            payload["order_id"]
        )

        if not order:
            return

        await delivery_lifecycle_service.create_delivery(
            db=db,
            order=order
        )