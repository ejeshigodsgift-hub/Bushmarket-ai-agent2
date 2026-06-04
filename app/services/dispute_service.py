from decimal import Decimal
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.payment_transaction import PaymentTransaction
from app.db.models.order import Order
from app.db.models.refund import Refund
from app.db.models.audit_log import AuditLog

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from app.services.idempotency_service import idempotency_service


class DisputeService:
    """
    Handles chargebacks, disputes, refunds, and resolution flow.
    """

    def __init__(self):
        self.audit = AuditService()

    # =========================================================
    # CREATE DISPUTE
    # =========================================================
    async def create_dispute(
        self,
        db: AsyncSession,
        payment_transaction_id: str,
        order_id: str,
        reason: str,
        reference: str,
        user_id: str,
        ip_address: str | None = None,
        device_id: str | None = None,
    ):
        await self._ensure_idempotent(db, reference)

        tx = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.id == payment_transaction_id
            )
        )
        tx = tx.scalar_one_or_none()

        if not tx:
            raise HTTPException(404, "Payment transaction not found")

        order = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = order.scalar_one_or_none()

        if not order:
            raise HTTPException(404, "Order not found")

        tx.status = "disputed"

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="dispute_created",
            entity_type="payment_transaction",
            entity_id=tx.id,
            reference=reference,
            metadata={
                "reason": reason,
                "order_id": order_id,
                "payment_transaction_id": payment_transaction_id
            },
            ip_address=ip_address,
            device_id=device_id
        )

        await outbox_service.queue_event(
            db=db,
            topic="dispute.created",
            payload={
                "payment_transaction_id": tx.id,
                "order_id": order_id,
                "reason": reason,
                "reference": reference
            }
        )

        return tx

    # =========================================================
    # START INVESTIGATION
    # =========================================================
    async def mark_investigating(
        self,
        db: AsyncSession,
        payment_transaction_id: str,
        reference: str
    ):
        await self._ensure_idempotent(db, reference)

        tx = await self._get_tx(db, payment_transaction_id)

        tx.status = "investigating"

        await self.audit.log(
            db=db,
            user_id="system",
            action="dispute_investigating",
            entity_type="payment_transaction",
            entity_id=tx.id,
            reference=reference,
            metadata={}
        )

        await outbox_service.queue_event(
            db=db,
            topic="dispute.investigating",
            payload={"payment_transaction_id": tx.id}
        )

        return tx

    # =========================================================
    # AUTO REFUND (IF VALID DISPUTE)
    # =========================================================
    async def issue_refund(
        self,
        db: AsyncSession,
        payment_transaction_id: str,
        order_id: str,
        amount: Decimal,
        reason: str,
        reference: str,
        processed_by: str | None = None
    ):
        await self._ensure_idempotent(db, reference)

        tx = await self._get_tx(db, payment_transaction_id)

        refund = Refund(
            order_id=order_id,
            payment_transaction_id=payment_transaction_id,
            amount=amount,
            refund_reference=reference,
            reason=reason,
            status="processing",
            processed_by=processed_by
        )

        db.add(refund)

        tx.status = "refunded"

        await self.audit.log(
            db=db,
            user_id=processed_by or "system",
            action="refund_issued",
            entity_type="refund",
            entity_id=refund.id,
            reference=reference,
            amount=float(amount),
            metadata={"reason": reason}
        )

        await outbox_service.queue_event(
            db=db,
            topic="refund.issued",
            payload={
                "refund_id": refund.id,
                "payment_transaction_id": payment_transaction_id,
                "amount": str(amount),
                "reference": reference
            }
        )

        return refund

    # =========================================================
    # RESOLVE DISPUTE (WIN / LOSS)
    # =========================================================
    async def resolve_dispute(
        self,
        db: AsyncSession,
        payment_transaction_id: str,
        result: str,  # won | lost
        reference: str,
        notes: str | None = None
    ):
        await self._ensure_idempotent(db, reference)

        tx = await self._get_tx(db, payment_transaction_id)

        if result not in ["won", "lost"]:
            raise HTTPException(400, "Invalid resolution")

        tx.status = f"chargeback_{result}"

        await self.audit.log(
            db=db,
            user_id="system",
            action="dispute_resolved",
            entity_type="payment_transaction",
            entity_id=tx.id,
            reference=reference,
            metadata={
                "result": result,
                "notes": notes
            }
        )

        await outbox_service.queue_event(
            db=db,
            topic="dispute.resolved",
            payload={
                "payment_transaction_id": tx.id,
                "result": result,
                "reference": reference
            }
        )

        return tx

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================
    async def _get_tx(self, db: AsyncSession, tx_id: str):
        tx = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.id == tx_id
            )
        )
        tx = tx.scalar_one_or_none()

        if not tx:
            raise HTTPException(404, "Transaction not found")

        return tx

    async def _ensure_idempotent(self, db: AsyncSession, reference: str):
        exists = await idempotency_service.exists(db=db, key=reference)

        if exists:
            raise HTTPException(409, "Duplicate reference")

        await idempotency_service.record(db=db, key=reference)