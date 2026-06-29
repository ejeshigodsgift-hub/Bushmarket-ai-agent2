from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.cooperative_membership_service import (
    CooperativeMembershipService
)

from app.services.outbox_service import outbox_service
from app.services.audit_service import AuditService

from app.integrations.financial_core import financial_core


class CooperativePaymentService:

    def __init__(self):
        self.audit = AuditService()

    # =========================================
    # INITIATE PAYMENT
    # =========================================
    async def initiate_membership_payment(
        self,
        db: AsyncSession,
        membership_id: str,
        user_id: str,
        amount: float,
        cooperative_id: str
    ):

        # send to financial core
        payment_intent = await financial_core.create_payment_intent(
            user_id=user_id,
            amount=amount,
            purpose="cooperative_membership",
            reference=f"coop_mem_{membership_id}"
        )

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.payment.initiated",
            payload={
                "membership_id": membership_id,
                "payment_intent_id": payment_intent["id"],
                "amount": amount
            }
        )

        await db.commit()

        return payment_intent

    # =========================================
    # PAYMENT SUCCESS WEBHOOK
    # =========================================
    async def handle_payment_success(
        self,
        db: AsyncSession,
        membership_id: str,
        payment_reference: str,
        user_id: str
    ):

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.payment.success",
            payload={
                "membership_id": membership_id,
                "payment_reference": payment_reference
            }
        )


        membership_service =  CooperativeMembershipService()

        await membership_service.activate_membership(
            db=db,
            membership_id=membership_id,
            payment_reference=payment_reference
        )

        await db.commit()

        return True

    # =========================================
    # PAYMENT FAILURE WEBHOOK
    # =========================================
    async def handle_payment_failed(
        self,
        db: AsyncSession,
        membership_id: str,
        reason: str = "payment_failed"
    ):

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.payment.failed",
            payload={
                "membership_id": membership_id,
                "reason": reason
            }
        )

        await db.commit()

        return True


cooperative_payment_service = CooperativePaymentService()