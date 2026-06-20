from decimal import Decimal

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.payment_intent import PaymentIntent
from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from app.services.idempotency_service import idempotency_service
from app.integrations.paystack_gateway import PaystackGateway
from app.services.payment_webhook_service import PaymentWebhookService

router = APIRouter(prefix="/webhooks", tags=["Payment Webhooks"])

gateway = PaystackGateway()
audit = AuditService()
payment_webhook_service = PaymentWebhookService()


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
        raise HTTPException(400, "Missing reference")

    # =========================================
    # IDEMPOTENCY
    # =========================================
    key = idempotency_service.generate_key(
        reference=reference,
        action="paystack_webhook"
    )

    if await idempotency_service.is_processed(db=db, key=key):
        return {"status": "already_processed"}

    # =========================================
    # VERIFY PAYMENT
    # =========================================
    verification = await gateway.verify_payment(reference=reference)
    verified_data = verification.get("data", {})

    if verified_data.get("status") != "success":
        raise HTTPException(400, "Payment verification failed")

    stmt = select(PaymentIntent).where(
        PaymentIntent.reference == reference
    )

    result = await db.execute(stmt)
    intent = result.scalar_one_or_none()

    if not intent:
        raise HTTPException(404, "Payment intent not found")

    amount = Decimal(str(verified_data.get("amount", 0))) / Decimal("100")

    # =========================================
    # ONLY CALL SERVICE (NO BUSINESS LOGIC HERE)
    # =========================================
    await payment_webhook_service.handle_payment_success(
        db=db,
        payment_reference=reference,
        gateway="paystack",
        amount=float(amount),
        user_id=intent.user_id
    )

    await idempotency_service.mark_processed(
        db=db,
        key=key,
        reference=reference,
        action="paystack_webhook"
    )

    await db.commit()

    return {"status": "processed"}

    # =========================================
    # MARK IDEMPOTENCY
    # =========================================
    await idempotency_service.mark_processed(
        db=db,
        key=key,
        reference=reference,
        action="paystack_webhook"
    )

    await db.commit()

    return {"status": "processed"}