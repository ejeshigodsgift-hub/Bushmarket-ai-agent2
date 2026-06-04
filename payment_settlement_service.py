# app/services/payment_settlement_service.py

from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.payment_intent import PaymentIntent
from app.db.models.escrow_account import EscrowAccount

from app.services.financial_core_service import FinancialCoreService
from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from app.services.idempotency_service import idempotency_service


class PaymentSettlementService:
    """
    FINAL PAYMENT SETTLEMENT ORCHESTRATOR

    Flow:
    Gateway → Webhook → Intent → Escrow → Ledger → Wallet
    """

    def __init__(self):
        self.financial_core = FinancialCoreService()
        self.audit = AuditService()

    # =====================================================
    # MAIN ENTRY POINT
    # =====================================================
    async def settle_payment(
        self,
        db: AsyncSession,
        reference: str,
        amount: Decimal,
        gateway: str,
        user_id: str
    ):
        """
        Entry point after webhook verification
        """

        # 1. IDEMPOTENCY GUARD
        await idempotency_service.ensure(
            db=db,
            key=reference
        )

        # 2. LOAD PAYMENT INTENT
        stmt = select(PaymentIntent).where(
            PaymentIntent.reference == reference
        )

        intent = (await db.execute(stmt)).scalar_one_or_none()

        if not intent:
            raise ValueError("Payment intent not found")

        # 3. MARK INTENT PROCESSING
        intent.status = "processing"

        # =====================================================
        # 4. ROUTE SETTLEMENT LOGIC
        # =====================================================

        if intent.purpose == "wallet_topup":
            return await self._settle_wallet_topup(
                db, intent, reference, amount
            )

        if intent.purpose == "escrow_fund":
            return await self._settle_escrow_fund(
                db, intent, reference, amount
            )

        if intent.purpose == "cooperative_membership":
            return await self._settle_cooperative(
                db, intent, reference, amount
            )

        raise ValueError(f"Unknown purpose: {intent.purpose}")

    # =====================================================
    # WALLET TOPUP SETTLEMENT
    # =====================================================
    async def _settle_wallet_topup(
        self,
        db: AsyncSession,
        intent: PaymentIntent,
        reference: str,
        amount: Decimal
    ):

        # 1. ESCROW DEPOSIT FIRST (SAFETY LAYER)
        escrow = await db.execute(
            select(EscrowAccount).limit(1)
        )

        escrow_account = escrow.scalar_one_or_none()

        if not escrow_account:
            raise ValueError("Escrow account missing")

        await self.financial_core.escrow_deposit(
            db=db,
            escrow_id=escrow_account.id,
            amount=amount,
            reference=reference,
            debit_ledger_account="cash_in",
            credit_ledger_account="escrow_liability"
        )

        # 2. WALLET CREDIT
        await self.financial_core.wallet_credit(
            db=db,
            wallet_id=intent.user_id,
            amount=amount,
            reference=reference,
            debit_ledger_account="escrow_liability",
            credit_ledger_account="wallet_liability"
        )

        # 3. UPDATE STATUS
        intent.status = "successful"

        # 4. OUTBOX EVENT
        await outbox_service.queue_event(
            db=db,
            topic="settlement.wallet.completed",
            payload={
                "user_id": intent.user_id,
                "amount": str(amount),
                "reference": reference
            }
        )

        # 5. AUDIT
        await self.audit.log(
            db=db,
            user_id=intent.user_id,
            action="wallet_settled",
            entity_type="payment_intent",
            entity_id=intent.id,
            reference=reference,
            amount=float(amount)
        )

        return intent

    # =====================================================
    # ESCROW FUND SETTLEMENT
    # =====================================================
    async def _settle_escrow_fund(
        self,
        db: AsyncSession,
        intent: PaymentIntent,
        reference: str,
        amount: Decimal
    ):

        escrow = await db.execute(
            select(EscrowAccount).limit(1)
        )

        escrow_account = escrow.scalar_one_or_none()

        if not escrow_account:
            raise ValueError("Escrow not found")

        await self.financial_core.escrow_deposit(
            db=db,
            escrow_id=escrow_account.id,
            amount=amount,
            reference=reference,
            debit_ledger_account="cash_in",
            credit_ledger_account="escrow_liability"
        )

        intent.status = "successful"

        await outbox_service.queue_event(
            db=db,
            topic="settlement.escrow.completed",
            payload={
                "escrow_id": escrow_account.id,
                "amount": str(amount),
                "reference": reference
            }
        )

        return intent

    # =====================================================
    # COOPERATIVE MEMBERSHIP SETTLEMENT
    # =====================================================
    async def _settle_cooperative(
        self,
        db: AsyncSession,
        intent: PaymentIntent,
        reference: str,
        amount: Decimal
    ):

        escrow = await db.execute(
            select(EscrowAccount).where(
                EscrowAccount.cooperative_id.isnot(None)
            )
        )

        escrow_account = escrow.scalar_one_or_none()

        if not escrow_account:
            raise ValueError("Cooperative escrow missing")

        await self.financial_core.escrow_deposit(
            db=db,
            escrow_id=escrow_account.id,
            amount=amount,
            reference=reference,
            debit_ledger_account="cash_in",
            credit_ledger_account="cooperative_fund"
        )

        intent.status = "successful"

        await outbox_service.queue_event(
            db=db,
            topic="settlement.cooperative.completed",
            payload={
                "user_id": intent.user_id,
                "amount": str(amount),
                "reference": reference
            }
        )

        return intent