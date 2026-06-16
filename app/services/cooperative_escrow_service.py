from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.escrow_transaction import EscrowTransaction

from app.services.financial_core_service import FinancialCoreService
from app.services.outbox_service import outbox_service


class CooperativeEscrowService:
    """
    COOPERATIVE ESCROW ORCHESTRATION LAYER

    FinancialCoreService remains the ONLY source of truth
    for money movement, balances, escrow state and ledger entries.

    This service:
    - coordinates cooperative workflows
    - logs cooperative escrow transactions
    - emits cooperative domain events
    """

    def __init__(self):
        self.financial = FinancialCoreService()

    # =========================================================
    # ESCROW DEPOSIT
    # =========================================================

    async def deposit(
        self,
        db: AsyncSession,
        escrow_id: str,
        amount: Decimal,
        reference: str,
        debit_ledger_account: str,
        credit_ledger_account: str
    ):
        escrow = await self.financial.escrow_deposit(
            db=db,
            escrow_id=escrow_id,
            amount=amount,
            reference=reference,
            debit_ledger_account=debit_ledger_account,
            credit_ledger_account=credit_ledger_account
        )

        tx = self._log_tx(
            escrow_id=escrow.id,
            tx_type="deposit",
            amount=amount,
            reference=reference
        )

        await self._emit(
            db=db,
            topic="cooperative.escrow.deposit",
            tx=tx
        )

        return escrow

    # =========================================================
    # HOLD
    # =========================================================

    async def hold(
        self,
        db: AsyncSession,
        escrow_id: str,
        amount: Decimal,
        reference: str,
        reserved_ledger_account: str,
        available_ledger_account: str
    ):
        escrow = await self.financial.escrow_hold(
            db=db,
            escrow_id=escrow_id,
            amount=amount,
            reference=reference,
            reserved_ledger_account=reserved_ledger_account,
            available_ledger_account=available_ledger_account
        )

        tx = self._log_tx(
            escrow_id=escrow.id,
            tx_type="hold",
            amount=amount,
            reference=reference
        )

        await self._emit(
            db=db,
            topic="cooperative.escrow.hold",
            tx=tx
        )

        return escrow

    # =========================================================
    # UNHOLD
    # =========================================================

    async def unhold(
        self,
        db: AsyncSession,
        escrow_id: str,
        amount: Decimal,
        reference: str,
        reserved_ledger_account: str,
        available_ledger_account: str
    ):
        escrow = await self.financial._lock_escrow(
            db,
            escrow_id
        )

        if escrow.total_reserved < amount:
            raise HTTPException(
                status_code=400,
                detail="Insufficient reserved balance"
            )

        escrow.total_reserved -= amount
        escrow.available_balance += amount
        escrow.version += 1

        await self.financial._post_double_entry(
            db=db,
            debit_account_id=available_ledger_account,
            credit_account_id=reserved_ledger_account,
            amount=amount,
            reference=reference,
            description="Escrow Unhold"
        )

        tx = self._log_tx(
            escrow.id,
            "unhold",
            amount,
            reference
        )

        await self._emit(
            db,
            "cooperative.escrow.unhold",
            tx
        )

        return escrow

    # =========================================================
    # RELEASE
    # =========================================================

    async def release(
        self,
        db: AsyncSession,
        escrow_id: str,
        amount: Decimal,
        reference: str,
        settlement_ledger_account: str,
        reserved_ledger_account: str
    ):
        escrow = await self.financial.escrow_release(
            db=db,
            escrow_id=escrow_id,
            amount=amount,
            reference=reference,
            settlement_ledger_account=settlement_ledger_account,
            reserved_ledger_account=reserved_ledger_account
        )

        tx = self._log_tx(
            escrow_id=escrow.id,
            tx_type="release",
            amount=amount,
            reference=reference
        )

        await self._emit(
            db=db,
            topic="cooperative.escrow.release",
            tx=tx
        )

        return escrow

    # =========================================================
    # REFUND
    # =========================================================

    async def refund(
        self,
        db: AsyncSession,
        escrow_id: str,
        amount: Decimal,
        reference: str
    ):
        escrow = await self.financial.escrow_refund(
            db=db,
            escrow_id=escrow_id,
            amount=amount,
            reference=reference
        )

        tx = self._log_tx(
            escrow_id=escrow.id,
            tx_type="refund",
            amount=amount,
            reference=reference
        )

        await self._emit(
            db=db,
            topic="cooperative.escrow.refund",
            tx=tx
        )

        return escrow

    # =========================================================
    # HELPERS
    # =========================================================

    def _log_tx(
        self,
        escrow_id: str,
        tx_type: str,
        amount: Decimal,
        reference: str
    ):
        return EscrowTransaction(
            escrow_account_id=escrow_id,
            transaction_type=tx_type,
            amount=amount,
            reference=reference,
            status="successful"
        )

    async def _emit(
        self,
        db: AsyncSession,
        topic: str,
        tx: EscrowTransaction
    ):
        db.add(tx)

        await outbox_service.queue_event(
            db=db,
            topic=topic,
            payload={
                "escrow_id": tx.escrow_account_id,
                "type": tx.transaction_type,
                "amount": str(tx.amount),
                "reference": tx.reference
            }
        )