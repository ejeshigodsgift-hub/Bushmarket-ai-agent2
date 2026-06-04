from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.financial_core_service import FinancialCoreService
from app.services.payment_webhook_service import payment_webhook_service
from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from app.services.idempotency_service import idempotency_service


class IntegrationService:
    """
    BUSHMARKET INTEGRATION LAYER

    PURPOSE:
    - Single orchestration entry point for:
        • Payment confirmation flows
        • Wallet topups
        • Escrow funding
        • Cooperative payments
        • Ledger synchronization
    - Decouples API/webhooks from financial core logic
    """

    def __init__(self):
        self.financial_core = FinancialCoreService()
        self.audit = AuditService()

    # =====================================================
    # PAYMENT SUCCESS ENTRY POINT (MAIN ORCHESTRATOR)
    # =====================================================
    async def handle_payment_success(
        self,
        db: AsyncSession,
        reference: str,
        gateway: str,
        amount: Decimal,
        user_id: str,
        purpose: str,
        metadata: dict | None = None
    ):
        """
        SINGLE ENTRY POINT FOR ALL PAYMENT COMPLETION EVENTS
        """

        # 1. IDEMPOTENCY GUARD
        await idempotency_service.ensure(
            db=db,
            key=reference
        )

        # 2. ROUTE BASED ON PURPOSE
        if purpose == "wallet_topup":
            return await self._wallet_topup_flow(
                db, reference, amount, user_id
            )

        if purpose == "escrow_fund":
            return await self._escrow_fund_flow(
                db, reference, amount, metadata
            )

        if purpose == "cooperative_membership":
            return await self._cooperative_flow(
                db, reference, amount, user_id
            )

        raise ValueError(f"Unknown payment purpose: {purpose}")

    # =====================================================
    # WALLET TOPUP FLOW
    # =====================================================
    async def _wallet_topup_flow(
        self,
        db: AsyncSession,
        reference: str,
        amount: Decimal,
        user_id: str
    ):
        """
        Gateway → Escrow → Wallet Credit
        """

        await self.financial_core.wallet_credit(
            db=db,
            wallet_id=user_id,  # assumed mapped
            amount=amount,
            reference=reference,
            debit_ledger_account="cash_in",
            credit_ledger_account="wallet_liability"
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="wallet_topup_completed",
            entity_type="wallet",
            entity_id=user_id,
            reference=reference,
            amount=float(amount)
        )

        await outbox_service.queue_event(
            db=db,
            topic="integration.wallet.topup.completed",
            payload={
                "user_id": user_id,
                "amount": str(amount),
                "reference": reference
            }
        )

    # =====================================================
    # ESCROW FUND FLOW
    # =====================================================
    async def _escrow_fund_flow(
        self,
        db: AsyncSession,
        reference: str,
        amount: Decimal,
        metadata: dict | None
    ):
        """
        Payment → Escrow Deposit (Marketplace Hold)
        """

        escrow_id = metadata.get("escrow_id") if metadata else None

        if not escrow_id:
            raise ValueError("Escrow ID required for escrow fund flow")

        await self.financial_core.escrow_deposit(
            db=db,
            escrow_id=escrow_id,
            amount=amount,
            reference=reference,
            debit_ledger_account="cash_in",
            credit_ledger_account="escrow_liability"
        )

        await outbox_service.queue_event(
            db=db,
            topic="integration.escrow.funded",
            payload={
                "escrow_id": escrow_id,
                "amount": str(amount),
                "reference": reference
            }
        )

    # =====================================================
    # COOPERATIVE MEMBERSHIP FLOW
    # =====================================================
    async def _cooperative_flow(
        self,
        db: AsyncSession,
        reference: str,
        amount: Decimal,
        user_id: str
    ):
        """
        Payment → Cooperative escrow allocation
        """

        await self.financial_core.escrow_deposit(
            db=db,
            escrow_id="cooperative_master_escrow",
            amount=amount,
            reference=reference,
            debit_ledger_account="cash_in",
            credit_ledger_account="cooperative_fund"
        )

        await outbox_service.queue_event(
            db=db,
            topic="integration.cooperative.membership",
            payload={
                "user_id": user_id,
                "amount": str(amount),
                "reference": reference
            }
        )