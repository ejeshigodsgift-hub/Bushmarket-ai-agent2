

from decimal import Decimal

from fastapi import (
APIRouter,
Request,
HTTPException,
Depends
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db

from app.db.models.payment_intent import PaymentIntent
from app.db.models.payment_transaction import PaymentTransaction

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from app.services.idempotency_service import idempotency_service

from app.integrations.paystack_gateway import PaystackGateway

router = APIRouter(
prefix="/webhooks",
tags=["Payment Webhooks"]
)

audit = AuditService()
gateway = PaystackGateway()

@router.post("/paystack")
async def paystack_webhook(
request: Request,
db: AsyncSession = Depends(get_db)
):

payload = await request.json()

event = payload.get("event")

if event != "charge.success":
    return {"status": "ignored"}

data = payload.get("data", {})

reference = data.get("reference")

if not reference:
    raise HTTPException(
        status_code=400,
        detail="Missing reference"
    )

idempotency_key = (
    idempotency_service.generate_key(
        reference=reference,
        action="paystack_webhook"
    )
)

already_processed = (
    await idempotency_service.is_processed(
        db=db,
        key=idempotency_key
    )
)

if already_processed:
    return {"status": "already_processed"}

verification = (
    await gateway.verify_payment(
        reference=reference
    )
)

verified_data = (
    verification.get("data", {})
)

if verified_data.get("status") != "success":
    raise HTTPException(
        status_code=400,
        detail="Payment verification failed"
    )

stmt = select(PaymentIntent).where(
    PaymentIntent.reference == reference
)

result = await db.execute(stmt)

payment_intent = (
    result.scalar_one_or_none()
)

if not payment_intent:
    raise HTTPException(
        status_code=404,
        detail="Payment intent not found"
    )

payment_intent.status = "completed"

payment_tx = PaymentTransaction(
    payment_intent_id=payment_intent.id,
    reference=reference,
    amount=Decimal(
        str(
            verified_data.get(
                "amount",
                0
            )
        )
    ) / Decimal("100"),
    currency=verified_data.get(
        "currency",
        "NGN"
    ),
    status="successful",
    gateway="paystack"
)

db.add(payment_tx)

await idempotency_service.mark_processed(
    db=db,
    key=idempotency_key,
    reference=reference,
    action="paystack_webhook"
)

await audit.log(
    db=db,
    user_id=payment_intent.user_id,
    action="payment_completed",
    entity_type="payment_intent",
    entity_id=payment_intent.id,
    reference=reference,
    amount=float(payment_tx.amount)
)

await outbox_service.queue_event(
    db=db,
    topic="payment.completed",
    payload={
        "payment_intent_id":
            payment_intent.id,
        "payment_transaction_id":
            payment_tx.id,
        "reference":
            reference,
        "amount":
            str(payment_tx.amount),
        "user_id":
            payment_intent.user_id
    }
)

await db.commit()

return {
    "status": "processed"
}