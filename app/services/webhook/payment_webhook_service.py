from datetime import datetime, timezone
from decimal import Decimal

from app.db.models.order import Order
from app.services.inventory_service import InventoryService
from app.db.models.checkout import Checkout

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.payment_intent import PaymentIntent
from app.db.models.payment_transaction import PaymentTransaction
from app.db.models.escrow_account import EscrowAccount

from app.services.payment_service import PaymentService
from app.services.financial_core_service import FinancialCoreService
from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service

from app.services.idempotency_service import IdempotencyService


class PaymentWebhookService:
    """
    Handles gateway callbacks (Paystack / Flutterwave)
    Production-grade financial entry point
    """

    def __init__(self):
        self.payment_service = PaymentService()
        self.financial_core = FinancialCoreService()
        self.audit = AuditService()
        self.inventory_service = InventoryService()
        self.idempotency_service = IdempotencyService()

    # =====================================================
    # MAIN WEBHOOK ENTRY POINT
    # =====================================================
    async def handle_payment_success(
        self,
        db: AsyncSession,
        payment_reference: str,
        gateway: str,
        amount: float,
        user_id: str
    ):


        already_processed = await self.idempotency_service.is_processed(
            db=db,
            key=payment_reference
        )

        if already_processed:
            return {"status":    "already_processed"}

        
        

        """
        Triggered ONLY after gateway confirms payment success
        """
            
        

        # =========================================
        # 1. FETCH INTENT
        # =========================================
        stmt = (
            select(PaymentIntent)
            .where(PaymentIntent.reference == payment_reference)
            .with_for_update()
        )

        result = await db.execute(stmt)
        intent = result.scalar_one_or_none()

        if not intent:
            raise HTTPException(404, "Payment intent not found")

        if Decimal(str(amount)) != intent.amount:  
            raise HTTPException(  
                400,  
                "Payment amount mismatch"  
           )  
  
  
        # =========================================
        # 2. IDEMPOTENCY GUARD
        # =========================================
        existing_tx = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.gateway_reference == payment_reference,
                PaymentTransaction.status == "successful"
            )
        )

        if existing_tx.scalar_one_or_none():
            return {"message": "Already processed"}

        # =========================================
        # 3. UPDATE PAYMENT INTENT
        # =========================================
        intent.status = "successful"

        # record transaction FIRST
        payment_tx = await  self.payment_service.record_transaction(
            db=db,
            intent_id=intent.id,
            gateway=gateway,
            amount=amount,
             gateway_reference=payment_reference,
            status="successful"
        )



        # =========================================
        # 4. ROUTE BASED ON PURPOSE
        # =========================================
        if intent.purpose == "wallet_topup":

            await self._handle_wallet_topup(
                db=db,
                intent=intent,
                reference=payment_reference,
                amount=amount
            )

        elif intent.purpose == "cooperative_membership":

            await self._handle_cooperative_membership(
                db=db,
                intent=intent,
                reference=payment_reference,
                amount=amount
            )

        elif intent.purpose == "escrow_fund":

            await self._handle_escrow_fund(
                db=db,
                intent=intent,
                reference=payment_reference,
                amount=amount
            )

        elif intent.purpose == "order":

            await self._handle_order_payment(
                db=db,
                intent=intent,
                reference=payment_reference,
                amount=amount
            )

        # =========================================
        # 5. AUDIT LOG
        # =========================================
        await self.audit.log(
            db=db,
            user_id=user_id,
            action="payment_webhook_success",
            entity_type="payment",
            entity_id=intent.id,
            metadata={
                "reference": payment_reference,
                "amount": amount,
                "purpose": intent.purpose
            },
            reference=payment_reference,
            amount=amount
        )

        # =========================================
        # 6. OUTBOX EVENT
        # =========================================
        await outbox_service.queue_event(
            db=db,
            topic="payment.webhook.successful",
            payload={
                "intent_id": intent.id,
                "reference": payment_reference,
                "purpose": intent.purpose,
                "amount": amount
            }
        )

        
        await  self.idempotency_service.mark_processed(
            db=db,
            key=payment_reference
        )



        
        return {"status": "processed"}

        

    # =====================================================
    # WALLET TOPUP FLOW
    # =====================================================
    async def _handle_wallet_topup(
        self,
        db: AsyncSession,
        intent: PaymentIntent,
        reference: str,
        amount: float
    ):


            # 2. ESCROW FETCH
            escrow = await db.execute(
                select(EscrowAccount)
                .where(EscrowAccount.type == "wallet")
                .limit(1)
            )

            escrow_account =    escrow.scalar_one_or_none()

            if not escrow_account:
                raise HTTPException(400,  "Escrow account missing")

            # 3. ESCROW DEPOSIT
            await self.financial_core.escrow_deposit(
                db=db,
                escrow_id=escrow_account.id,
                amount=amount,
                reference=reference
            )

            # 4. WALLET CREDIT
            await self.financial_core.credit_wallet(
                db=db,
                user_id=intent.user_id,
                amount=amount,
                reference=reference
            )

    # =====================================================
    # COOPERATIVE MEMBERSHIP FLOW
    # =====================================================
    async def _handle_cooperative_membership(
        self,
        db: AsyncSession,
        intent: PaymentIntent,
        reference: str,
        amount: float
    ):
        """
        Gateway → Escrow ONLY
        Activation happens AFTER validation
        """

        escrow = await db.execute(
            select(EscrowAccount).where(
                EscrowAccount.type == "cooperative"
            )
        )

        escrow_account = escrow.scalar_one_or_none()

        if not escrow_account:
            raise HTTPException(400, "Cooperative escrow missing")

        await self.financial_core.escrow_deposit(
            db=db,
            escrow_id=escrow_account.id,
            amount=amount,
            reference=reference
        )

    # =====================================================
    # ESCROW FUND FLOW (GENERAL MARKETPLACE)
    # =====================================================
    async def _handle_escrow_fund(
        self,
        db: AsyncSession,
        intent: PaymentIntent,
        reference: str,
        amount: float
    ):
        """
        Direct escrow funding for orders or marketplace holds
        """

        escrow = await db.execute(
            select(EscrowAccount).limit(1)
        )

        escrow_account = escrow.scalar_one_or_none()

        if not escrow_account:
            raise HTTPException(400, "Escrow not found")

        await self.financial_core.escrow_deposit(
            db=db,
            escrow_id=escrow_account.id,
            amount=amount,
            reference=reference
        )



    # =====================================================
# ORDER PAYMENT FLOW
# =====================================================
    async def _handle_order_payment(
        self,
        db: AsyncSession,
        intent: PaymentIntent,
        reference: str,
        amount: float
    ):
        """
        Gateway → Order fulfillment flow (Bushmarket standard)
        """

    # 1. LOAD ORDER
        if not intent.order_id:
            raise HTTPException(
                status_code=400,
                detail="Order not attached to payment intent"
            )

        order = await db.get(Order,  intent.order_id)

        if not order:
            raise HTTPException(404, "Order not found")

    # 2. VALIDATE ORDER + CHECKOUT
        checkout = await db.get(Checkout,  intent.checkout_id)

        if not checkout:
            raise HTTPException(404,  "Checkout not found")

         

    # 3. GUARD (IDEMPOTENCY)
        if order.payment_status == "paid":
            return

    # 4. REDUCE STOCK
        for item in order.items:
            await self.inventory_service.reduce_stock(
                db=db,
                listing_id=item.listing_id,
                quantity=item.quantity,
                order_id=order.id   
            )

    # 5. MARK ORDER PAID
        order.payment_status = "paid"
        order.payment_reference = reference

        if order.status == "pending":
            order.status = "processing"

    # 6. MARK CHECKOUT COMPLETED
        checkout.status = "completed"
        checkout.is_locked = False

        checkout.payment_status = "paid"
        checkout.payment_reference = reference
        checkout.completed_at = datetime.now(timezone.utc)

    # 7. ESCROW HOLD (FINAL SETTLEMENT STEP)
        escrow = await db.execute(
            select(EscrowAccount).limit(1)
        )

        escrow_account =  escrow.scalar_one_or_none()

        if not escrow_account:
            raise HTTPException(
                status_code=400,
                detail="Escrow account not found"
            )

        await self.financial_core.escrow_deposit(
            db=db,
            escrow_id=escrow_account.id,
            amount=amount,
            reference=reference
        )

    # 8. EMIT EVENTS
        await db.flush()

        await outbox_service.queue_event(
            db=db,
            topic="marketplace.order.paid",
            payload={
                "order_id": order.id,
                "order_number": order.order_number,
                "user_id": order.user_id,
                "reference": reference,
                "amount": amount
            }
        )

        await outbox_service.queue_event(
            db=db,
            topic="order.payment.completed",
            payload={
                  "order_id": order.id,
                "intent_id": intent.id,
                "user_id": intent.user_id,
                "reference": reference,
                "amount": amount
            }
        )

        

payment_webhook_service = PaymentWebhookService()