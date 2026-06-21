from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.inventory import Inventory

from app.services.inventory_service import InventoryService
from app.services.payment_webhook_service import PaymentWebhookService
from app.services.outbox_service import outbox_service


class OrderCancellationService:

    def __init__(self):
        self.inventory_service = InventoryService()
        self.payment_service = PaymentWebhookService()

    # =====================================
    # CANCEL ORDER
    # =====================================
    async def cancel_order(
        self,
        db: Session,
        order_id: str,
        user_id: str,
        reason: str = "user_request"
    ):
        """
        Cancels order + restores inventory
        """

        order = await db.get(Order, order_id)

        if not order:
            raise HTTPException(404, "Order not found")

        if order.status in ["shipped", "delivered"]:
            raise HTTPException(400, "Cannot cancel shipped order")

        if order.status == "cancelled":
            return {"message": "Order already cancelled"}

        # =====================================
        # LOAD ORDER ITEMS
        # =====================================
        stmt = select(OrderItem).where(
            OrderItem.order_id == order.id
        )

        items = (await db.execute(stmt)).scalars().all()

        # =====================================
        # RESTORE INVENTORY
        # =====================================
        for item in items:

            inventory = await db.get(Inventory, item.inventory_id)

            if inventory:
                self.inventory_service.cancel_reservation(
                    db=db,
                    inventory=inventory,
                    quantity=item.quantity,
                    user_id=user_id,
                    reason="order_cancelled"
                )

        # =====================================
        # UPDATE ORDER STATUS
        # =====================================
        order.status = "cancelled"
        order.is_cancelled = True

        # =====================================
        # EVENTS
        # =====================================
        if order.payment_status == "paid":
            await outbox_service.queue_event(
                db=db,
                topic="order.cancelled.paid",
                payload={
                    "order_id": order.id,
                    "user_id": order.user_id,
                    "reason": reason
                }
            )
        else:
            await outbox_service.queue_event(
                db=db,
                topic="order.cancelled",
                payload={
                    "order_id": order.id,
                    "user_id": order.user_id,
                    "reason": reason
                }
            )

        return {"status": "cancelled"}