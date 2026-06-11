from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.escrow_account import EscrowAccount
from app.db.models.escrow_transaction import EscrowTransaction

from app.services.financial_core_service import FinancialCoreService
from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from app.services.idempotency_service import idempotency_service


class CooperativeEscrowService:
    """
    COOPERATIVE ESCROW ORCHESTRATION LAYER (SINGLE SOURCE OF TRUTH)

    CONSOLIDATES:
    - HoldService
    - EscrowService (partial overlap)
    - escrow_hold / escrow_release duplication in FinancialCoreService

    RESPONSIBILITIES:
    - deposit funds into escrow
    - hold (reserve) funds
    - unhold (release reservation)
    - release (settlement)
    - refund orchestration hook
    - escrow transaction logging
    - event emission
    """

    def __init__(self):
        self.financial = FinancialCoreService()
        self.audit = AuditService()

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
        await self._idempotent(db, reference)

        if amount <= 0:
            raise HTTPException(400, "Invalid deposit amount")

        escrow = await self.financial._lock_escrow(db, escrow_id)

        if escrow.is_frozen:
            raise HTTPException(400, "Escrow is frozen")

        escrow.total_deposited += amount
        escrow.available_balance += amount
        escrow.ledger_balance += amount
        escrow.version += 1

        await self.financial._post_double_entry(
            db=db,
            debit_account_id=debit_ledger_account,
            credit_account_id=credit_ledger_account,
            amount=amount,
            reference=reference,
            description="ESCROW DEPOSIT"
        )

        tx = self._log_tx(escrow.id, "deposit", amount, reference)
        await self._emit(db, "escrow.deposit", tx)

        await self.audit.log(
            db=db,
            user_id="system",
            action="escrow_deposit",
            entity_type="escrow",
            entity_id=escrow.id,
            reference=reference,
            amount=float(amount)
        )

        return escrow

    # =========================================================
    # HOLD (RESERVE FUNDS)
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
        await self._idempotent(db, reference)

        if amount <= 0:
            raise HTTPException(400, "Invalid hold amount")

        escrow = await self.financial._lock_escrow(db, escrow_id)

        if escrow.available_balance < amount:
            raise HTTPException(400, "Insufficient available balance")

        escrow.available_balance -= amount
        escrow.total_reserved += amount
        escrow.version += 1

        await self.financial._post_double_entry(
            db=db,
            debit_account_id=reserved_ledger_account,
            credit_account_id=available_ledger_account,
            amount=amount,
            reference=reference,
            description="ESCROW HOLD"
        )

        tx = self._log_tx(escrow.id, "hold", amount, reference)
        await self._emit(db, "escrow.hold", tx)

        return escrow

    # =========================================================
    # UNHOLD (RELEASE RESERVATION BACK TO AVAILABLE)
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
        await self._idempotent(db, reference)

        if amount <= 0:
            raise HTTPException(400, "Invalid unhold amount")

        escrow = await self.financial._lock_escrow(db, escrow_id)

        if escrow.total_reserved < amount:
            raise HTTPException(400, "Insufficient reserved balance")

        escrow.total_reserved -= amount
        escrow.available_balance += amount
        escrow.version += 1

        await self.financial._post_double_entry(
            db=db,
            debit_account_id=available_ledger_account,
            credit_account_id=reserved_ledger_account,
            amount=amount,
            reference=reference,
            description="ESCROW UNHOLD"
        )

        tx = self._log_tx(escrow.id, "unhold", amount, reference)
        await self._emit(db, "escrow.unhold", tx)

        return escrow

    # =========================================================
    # RELEASE (SETTLEMENT)
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
        await self._idempotent(db, reference)

        if amount <= 0:
            raise HTTPException(400, "Invalid release amount")

        escrow = await self.financial._lock_escrow(db, escrow_id)

        if escrow.total_reserved < amount:
            raise HTTPException(400, "Insufficient reserved balance")

        escrow.total_reserved -= amount
        escrow.ledger_balance -= amount
        escrow.version += 1

        await self.financial._post_double_entry(
            db=db,
            debit_account_id=settlement_ledger_account,
            credit_account_id=reserved_ledger_account,
            amount=amount,
            reference=reference,
            description="ESCROW RELEASE"
        )

        tx = self._log_tx(escrow.id, "release", amount, reference)
        await self._emit(db, "escrow.release", tx)

        await self.audit.log(
            db=db,
            user_id="system",
            action="escrow_release",
            entity_type="escrow",
            entity_id=escrow.id,
            reference=reference,
            amount=float(amount)
        )

        return escrow

    # =========================================================
    # REFUND HOOK (DOMAIN ONLY — NO MONEY LOGIC HERE)
    # =========================================================
    async def refund_hook(
        self,
        db: AsyncSession,
        escrow_id: str,
        amount: Decimal,
        reference: str
    ):
        escrow = await self.financial._lock_escrow(db, escrow_id)

        if escrow.total_deposited < amount:
            raise HTTPException(400, "Invalid refund amount")

        tx = self._log_tx(escrow.id, "refund", amount, reference)
        await self._emit(db, "escrow.refund", tx)

        return escrow

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================
    async def _idempotent(self, db, reference: str):
        exists = await idempotency_service.exists(db=db, key=reference)
        if exists:
            raise HTTPException(409, "Duplicate operation")

        await idempotency_service.record(db=db, key=reference)

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

    async def _emit(self, db: AsyncSession, topic: str, tx: EscrowTransaction):
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