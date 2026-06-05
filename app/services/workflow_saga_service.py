

import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.checkout_service import CheckoutService
from app.services.order_service import OrderService
from app.services.escrow_service import EscrowService
from app.services.payment_service import PaymentService
from app.services.inventory_service import InventoryService
from app.services.outbox_service import outbox_service

class WorkflowSagaService:

def __init__(self):

    self.checkout_service = CheckoutService()
    self.order_service = OrderService()
    self.escrow_service = EscrowService()
    self.payment_service = PaymentService()
    self.inventory_service = InventoryService()

async def execute_checkout_workflow(
    self,
    db: AsyncSession,
    user_id: str,
    cart,
    escrow_account_id: str
):

    saga_id = str(uuid.uuid4())

    try:

        # STEP 1
        checkout = self.checkout_service.create_checkout(
            db=db,
            user_id=user_id,
            cart=cart
        )

        # STEP 2
        order = self.order_service.create_order(
            db=db,
            user_id=user_id,
            cart=cart
        )

        # STEP 3
        await self.escrow_service.deposit(
            db=db,
            escrow_account_id=escrow_account_id,
            amount=float(order.total_amount),
            reference=saga_id
        )

        # STEP 4
        payment_intent = await self.payment_service.create_payment_intent(
            db=db,
            user_id=user_id,
            amount=float(order.total_amount),
            purpose="market_order",
            reference=saga_id
        )

        # STEP 5
        await self.payment_service.mark_success(
            db=db,
            intent_id=payment_intent.id,
            gateway_reference=saga_id
        )

        # STEP 6
        order.status = "completed"
        order.payment_status = "paid"

        await outbox_service.queue_event(
            db=db,
            topic="workflow.order.completed",
            payload={
                "saga_id": saga_id,
                "order_id": order.id
            }
        )

        await db.commit()

        return {
            "saga_id": saga_id,
            "order_id": order.id,
            "status": "completed"
        }

    except Exception as e:

        await db.rollback()

        await outbox_service.queue_event(
            db=db,
            topic="workflow.order.failed",
            payload={
                "saga_id": saga_id,
                "reason": str(e)
            }
        )

        raise HTTPException(
            status_code=500,
            detail=f"Saga failed: {str(e)}"
        )