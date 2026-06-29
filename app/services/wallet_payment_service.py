from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.wallet import Wallet
from app.db.models.order import Order
from app.db.models.checkout import Checkout
from app.db.models.escrow_account import EscrowAccount

from app.db.seeds.system_cooperatives import (
MARKETPLACE_COOPERATIVE_ID,
)

from app.services.financial_core_service import (
FinancialCoreService
)

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service

class WalletPaymentService:

def __init__(self):
    self.financial_core = FinancialCoreService()
    self.audit = AuditService()

async def _get_marketplace_escrow(
    self,
    db: AsyncSession
) -> EscrowAccount:

    result = await db.execute(
        select(EscrowAccount).where(
            EscrowAccount.cooperative_id
            == MARKETPLACE_COOPERATIVE_ID
        )
    )

    escrow = result.scalar_one_or_none()

    if not escrow:
        raise HTTPException(
            status_code=404,
            detail="Marketplace escrow not found"
        )

    return escrow

async def pay_order_with_wallet(
    self,
    db: AsyncSession,
    user_id: str,
    order_id: str,
    wallet_id: str,
    reference: str
):

    # =====================================
    # ORDER
    # =====================================

    order = await db.get(Order, order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Order ownership mismatch"
        )

    if order.payment_status == "paid":
        return order

    # =====================================
    # WALLET
    # =====================================

    wallet = await db.get(
        Wallet,
        wallet_id
    )

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found"
        )

    if wallet.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Wallet ownership mismatch"
        )

    amount = Decimal(
        str(order.total_amount)
    )

    # =====================================
    # ESCROW
    # =====================================

    escrow = await self._get_marketplace_escrow(
        db
    )

    # =====================================
    # WALLET DEBIT
    # =====================================

    await self.financial_core.wallet_debit(
        db=db,
        wallet_id=wallet.id,
        amount=amount,
        reference=f"{reference}-WALLET",
        debit_ledger_account="wallet_liability",
        credit_ledger_account="marketplace_escrow"
    )

    # =====================================
    # ESCROW DEPOSIT
    # =====================================

    await self.financial_core.escrow_deposit(
        db=db,
        escrow_id=escrow.id,
        amount=amount,
        reference=f"{reference}-ESCROW",
        debit_ledger_account="marketplace_escrow",
        credit_ledger_account="escrow_liability"
    )

    # =====================================
    # ORDER UPDATE
    # =====================================

    order.payment_status = "paid"
    order.payment_reference = reference

    if order.status == "pending":
        order.status = "processing"

    # =====================================
    # CHECKOUT UPDATE
    # =====================================

    if order.checkout_id:

        checkout = await db.get(
            Checkout,
            order.checkout_id
        )

        if checkout:
            checkout.status = "completed"
            checkout.is_locked = False
            checkout.payment_status = "paid"
            checkout.payment_reference = reference
            checkout.completed_at = (
                datetime.now(timezone.utc)
            )

    # =====================================
    # AUDIT
    # =====================================

    await self.audit.log(
        db=db,
        user_id=user_id,
        action="wallet_order_payment",
        entity_type="order",
        entity_id=order.id,
        reference=reference,
        amount=float(amount)
    )

    # =====================================
    # EVENTS
    # =====================================

    await outbox_service.queue_event(
        db=db,
        topic="marketplace.order.wallet_paid",
        payload={
            "order_id": order.id,
            "user_id": user_id,
            "wallet_id": wallet.id,
            "amount": str(amount),
            "reference": reference
        }
    )

    await db.flush()

    return order

wallet_payment_service = WalletPaymentService()