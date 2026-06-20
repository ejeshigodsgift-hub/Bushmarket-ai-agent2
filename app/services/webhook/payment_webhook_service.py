from datetime import datetime, timezone

from app.db.models.order import Order
from app.services.inventory_service import InventoryService

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
        """
        Triggered ONLY after gateway confirms payment success
        """
            
        

        # =========================================
        # 1. FETCH INTENT
        # =========================================
        stmt = select(PaymentIntent).where(
            PaymentIntent.reference == payment_reference
        )
        intent = (await db.execute(stmt)).scalar_one_or_none()

        if not intent:
            raise HTTPException(404, "Payment intent not found")

        # =========================================
        # 2. IDEMPOTENCY GUARD
        # =========================================
        existing_tx = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.gateway_reference == payment_reference,
                PaymentTransaction.status == "success"
            )
        )

        if existing_tx.scalar_one_or_none():
            return {"message": "Already processed"}

        # =========================================
        # 3. UPDATE PAYMENT INTENT
        # =========================================
        intent.status = "successful"

        if intent.purpose == "order":
        await  self._handle_order_payment(...)

        # record gateway transaction
        await self.payment_service.record_transaction(
            db=db,
            intent_id=intent.id,
            gateway=gateway,
            amount=amount,
            gateway_reference=payment_reference,
            status="success"
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
            topic="payment.webhook.success",
            payload={
                "intent_id": intent.id,
                "reference": payment_reference,
                "purpose": intent.purpose,
                "amount": amount
            }
        )

        await db.commit()

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
        """
        Gateway → Escrow → Wallet credit (via FinancialCore)
        """

        # NOTE: escrow step (temporary holding)
        escrow = await db.execute(
            select(EscrowAccount).where(
                EscrowAccount.cooperative_id.is_(None)
            )
        )

        escrow_account = escrow.scalar_one_or_none()

        if not escrow_account:
            raise HTTPException(400, "Escrow account missing")

        await self.financial_core.escrow_deposit(
            db=db,
            escrow_id=escrow_account.id,
            amount=amount,
            reference=reference
        )

        # wallet credit handled after escrow validation
        # (in real system this is async or rule-based trigger)

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
                EscrowAccount.cooperative_id.isnot(None)
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
        Gateway → Escrow hold for     marketplace order
        """

        escrow = await db.execute(
            select(EscrowAccount).limit(1)
        )

        escrow_account =   escrow.scalar_one_or_none()

        if not escrow_account:
             raise HTTPException(
                 status_code=400,
                detail="Escrow account not found"
            )

        await   self.financial_core.escrow_deposit(
            db=db,
            escrow_id=escrow_account.id,
            amount=amount,
            reference=reference
        )


        

        if not intent.order_id:
            raise HTTPException(
                status_code=400,
                detail="Order not attached to payment intent"
            )

        order = await db.get(Order,   intent.order_id)

        if not order:
            raise HTTPException(404, "Order not found")

      
        if order.payment_status == "paid":
            return

        order.payment_status = "paid"
        order.payment_reference = reference

        for item in order.items:
            await  self.inventory_service.reduce_stock(
                db=db,
                listing_id=item.listing_id,
                quantity=item.quantity
            )

        if order.status == "pending":
            order.status = "processing"

        await db.flush()

        await outbox_service.queue_event(
            db=db,
            topic="marketplace.order.paid",
            payload={
                "order_id": order.id,
                "order_number":   order.order_number,
                "user_id": order.user_id,
                "reference": reference,
                "amount": amount
            }
        )

        await outbox_service.queue_event(
            db=db,
            topic="order.payment.completed",
            payload={
                "intent_id": intent.id,
                "user_id": intent.user_id,
                "reference": reference,
                "amount": amount
            }
        )

        await db.commit()      

payment_webhook_service = PaymentWebhookService()