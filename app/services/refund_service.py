from decimal import Decimal
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.payment_intent import PaymentIntent
from app.db.models.escrow_account import EscrowAccount
from app.db.models.escrow_transaction import EscrowTransaction

from app.services.financial_core_service import FinancialCoreService
from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service


class RefundService:
    """
    Handles full refund lifecycle across escrow + ledger system
    """

    def __init__(self):
        self.financial_core = FinancialCoreService()
        self.audit = AuditService()

    # =========================================
    # INITIATE REFUND
    # =========================================
    async def refund_payment(
        self,
        db: AsyncSession,
        payment_reference: str,
        amount: Decimal,
        reason: str,
        user_id: str
    ):

        # =========================================
        # 1. VALIDATE PAYMENT INTENT
        # =========================================
        stmt = select(PaymentIntent).where(
            PaymentIntent.reference == payment_reference
        )

        intent = (await db.execute(stmt)).scalar_one_or_none()

        if not intent:
            raise HTTPException(404, "Payment not found")

        if intent.status != "successful":
            raise HTTPException(400, "Cannot refund non-successful payment")

        # =========================================
        # 2. FETCH ESCROW
        # =========================================
        escrow_stmt = select(EscrowAccount).limit(1)
        escrow = (await db.execute(escrow_stmt)).scalar_one_or_none()

        if not escrow:
            raise HTTPException(404, "Escrow account not found")

        if escrow.available_balance < amount:
            raise HTTPException(400, "Insufficient escrow balance")

        # =========================================
        # 3. EXECUTE ESCROW REVERSAL
        # =========================================
        escrow.available_balance -= amount
        escrow.total_deposited -= amount
        escrow.version += 1

        tx = EscrowTransaction(
            escrow_account_id=escrow.id,
            transaction_type="refund",
            amount=amount,
            reference=payment_reference,
            metadata={
                "reason": reason,
                "refund_at": str(datetime.now(timezone.utc))
            }
        )

        db.add(tx)

        # =========================================
        # 4. AUDIT LOG
        # =========================================
        await self.audit.log(
            db=db,
            user_id=user_id,
            action="refund_processed",
            entity_type="payment",
            entity_id=intent.id,
            metadata={
                "reference": payment_reference,
                "amount": str(amount),
                "reason": reason
            },
            reference=payment_reference,
            amount=float(amount)
        )

        # =========================================
        # 5. OUTBOX EVENT
        # =========================================
        await outbox_service.queue_event(
            db=db,
            topic="refund.processed",
            payload={
                "payment_reference": payment_reference,
                "amount": str(amount),
                "reason": reason
            }
        )

        await db.commit()

        return {
            "status": "refunded",
            "reference": payment_reference
        }


refund_service = RefundService()