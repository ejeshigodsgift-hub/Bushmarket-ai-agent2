

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.delivery import Delivery
from app.db.models.order import Order
from app.services.outbox_service import outbox_service


class DeliveryLifecycleService:

    async def create_delivery(
        self,
        db: AsyncSession,
        order: Order
    ):
        delivery = Delivery(
            order_id=order.id,
            status="pending"
        )

        db.add(delivery)
        await db.flush()

        await outbox_service.queue_event(
            db=db,
            topic="delivery.created",
            payload={
                "delivery_id": delivery.id,
                "order_id": order.id
            }
        )

        return delivery

    async def assign_agent(
        self,
        db: AsyncSession,
        delivery: Delivery,
        agent_id: str
    ):
        delivery.agent_id = agent_id
        delivery.status = "assigned"

        return delivery

    async def mark_delivered(
        self,
        db: AsyncSession,
        delivery: Delivery,
        order: Order
    ):
        delivery.status = "delivered"
        delivery.delivered_at = datetime.now(timezone.utc)

        order.status = "delivered"
        order.is_delivered = True
        order.delivered_at = datetime.now(timezone.utc)

        await outbox_service.queue_event(
            db=db,
            topic="delivery.delivered",
            payload={
                "delivery_id": delivery.id,
                "order_id": order.id
            }
        )

        return delivery


delivery_lifecycle_service = DeliveryLifecycleService()