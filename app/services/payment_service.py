from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.payment_intent import PaymentIntent
from app.db.models.payment_transaction import PaymentTransaction

from app.services.outbox_service import outbox_service
from decimal import Decimal


class PaymentService:
    """
    Central payment orchestration service
    """

    # =========================================
    # CREATE PAYMENT INTENT
    # =========================================
    async def create_payment_intent(
        self,
        db: AsyncSession,
        user_id: str,
        amount: Decimal,
        purpose: str,
        reference: str,
        currency: str = "NGN",
        checkout_id: str | None = None,
        order_id: str | None = None
    ):

        intent = PaymentIntent(
            user_id=user_id,
            amount=amount,
            purpose=purpose,
            reference=reference,
            currency=currency,
            status="pending",
            checkout_id=checkout_id,
            order_id=order_id
        )

        db.add(intent)

        await outbox_service.queue_event(
            db=db,
            topic="payment.intent.created",
            payload={
                "intent_id": intent.id,
                "user_id": user_id,
                "amount": str(amount),
                "purpose": purpose,
                "checkout_id":  checkout_id,
                "order_id": order_id
            }
        )

        # await db.commit()
        # await db.refresh(intent)

        return intent

    # =========================================
    # RECORD GATEWAY RESPONSE
    # =========================================
    async def record_transaction(
        self,
        db: AsyncSession,
        intent_id: str,
        gateway: str,
        amount: Decimal,
        gateway_reference: str | None,
        status: str,
        failure_reason: str | None = None
    ):

        tx = PaymentTransaction(
            intent_id=intent_id,
            gateway=gateway,
            amount=amount,
            gateway_reference=gateway_reference,
            status=status,
            failure_reason=failure_reason
        )
        
        
        db.add(tx)
        await db.flush()

        await outbox_service.queue_event(
            db=db,
            topic="payment.transaction.updated",
            payload={
                "intent_id": intent_id,
                "status": status,
                "gateway_reference": gateway_reference
            }
        )

        
        await db.refresh(tx)

        return tx

    # =========================================
    # MARK INTENT SUCCESS
    # =========================================
    async def mark_success(
        self,
        db: AsyncSession,
        intent_id: str,
        gateway_reference: str
    ):

        intent = await db.get(PaymentIntent, intent_id)

        if not intent:
            raise HTTPException(404, "Payment intent not found")

        intent.status = "successful"

        await self.record_transaction(
            db=db,
            intent_id=intent_id,
            gateway="system",
            amount=intent.amount,
            gateway_reference=gateway_reference,
            status="successful"
        )

        await outbox_service.queue_event(
            db=db,
            topic="payment.successful",
            payload={
                "intent_id": intent_id,
                "reference": gateway_reference
            }
        )

        

        return True

    # =========================================
    # MARK INTENT FAILED
    # =========================================
    async def mark_failed(
        self,
        db: AsyncSession,
        intent_id: str,
        reason: str
    ):

        intent = await db.get(PaymentIntent, intent_id)

        if not intent:
            raise HTTPException(404, "Payment intent not found")

        intent.status = "failed"

        await self.record_transaction(
            db=db,
            intent_id=intent_id,
            gateway="system",
            amount=intent.amount,
            gateway_reference=None,
            status="failed",
            failure_reason=reason
        )

        await outbox_service.queue_event(
            db=db,
            topic="payment.failed",
            payload={
                "intent_id": intent_id,
                "reason": reason
            }
        )

        

        return True


payment_service = PaymentService()