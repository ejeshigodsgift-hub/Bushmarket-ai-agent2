from decimal import Decimal
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.wallet import Wallet
from app.db.models.ledger_account import LedgerAccount
from app.db.models.ledger_entry import LedgerEntry
from app.db.models.escrow_account import EscrowAccount

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from app.services.idempotency_service import idempotency_service


class FinancialCoreService:
    """
    REAL SOURCE OF TRUTH (BANK-GRADE FINANCIAL ENGINE)
    """

    def __init__(self):
        self.audit = AuditService()

    

    # =========================================================
    # ROW LOCK HELPERS (CONCURRENCY SAFE)
    # =========================================================
    async def _lock_wallet(self, db: AsyncSession, wallet_id: str):
        stmt = select(Wallet).where(Wallet.id == wallet_id).with_for_update()
        return (await db.execute(stmt)).scalar_one()

    async def _lock_escrow(self, db: AsyncSession, escrow_id: str):
        stmt = select(EscrowAccount).where(EscrowAccount.id == escrow_id).with_for_update()
        return (await db.execute(stmt)).scalar_one()

    async def _lock_ledger(self, db: AsyncSession, account_id: str):
        stmt = select(LedgerAccount).where(LedgerAccount.id == account_id).with_for_update()
        return (await db.execute(stmt)).scalar_one()

    # =========================================================
    # DOUBLE ENTRY CORE ENGINE (ATOMIC POSTING)
    # =========================================================
    async def post_ledger_entry(
        self,
        db: AsyncSession,
        debit_account: str,
        credit_account: str,
        amount: Decimal,
        reference: str,
        description: str | None = None
    ):

        await self._ensure_idempotent(
            db,
            reference
        )
        if amount <= 0:
            raise HTTPException(400, "Invalid amount")

        debit = LedgerEntry(
            account_id=debit_account,
            entry_type="debit",
            amount=amount,
            transaction_reference=reference,
            description=description
        )

        credit = LedgerEntry(
            account_id=credit_account,
            entry_type="credit",
            amount=amount,
            transaction_reference=reference,
            description=description
        )

        db.add_all([debit, credit])
        return debit, credit

    

    # =========================================================
    # ESCROW HOLD (RESERVE FUNDS)
    # =========================================================
    async def escrow_hold(
        self,
        db: AsyncSession,
        escrow_id: str,
        amount: Decimal,
        reference: str,
        reserved_ledger_account: str,
        available_ledger_account: str
    ):
        await self._ensure_idempotent(
            db,
            reference
        )

        if amount <= 0:
            raise HTTPException(
                400,
                "Invalid amount"
            )

        escrow = await self._lock_escrow(
            db,
            escrow_id
        )

        if escrow.available_balance < amount:
            raise HTTPException(
                400,
                "Insufficient escrow balance"
            )

        escrow.available_balance -= amount
        escrow.total_reserved += amount
        escrow.version += 1

        await self._post_double_entry(
            db=db,
            debit_account_id=reserved_ledger_account,
        credit_account_id=available_ledger_account,
            amount=amount,
            reference=reference,
            description="Escrow Hold"
        )

        await outbox_service.queue_event(
            db=db,    
            topic="financial.escrow.hold",
            payload={
                "escrow_id": escrow.id,
                "amount": str(amount),
                "reference": reference
            }
        )

        return escrow

    # =========================================================
    # ESCROW RELEASE (SETTLEMENT / PLATFORM PAYOUT)
    # =========================================================
    async def escrow_release(
        self,
        db: AsyncSession,
        escrow_id: str,
        amount: Decimal,
        reference: str
    ):
        await self._ensure_idempotent(
            db,
            reference
        )

        if amount <= 0:
            raise HTTPException(
                400,
                "Invalid amount"
            )
        escrow = await self._lock_escrow(db, escrow_id)

        if escrow.total_reserved < amount:
            raise HTTPException(400, "Insufficient reserved funds")

        escrow.total_reserved -= amount
        escrow.ledger_balance -= amount
        escrow.version += 1

        await self._post_double_entry(
            db=db,
      
           debit_account_id=settlement_ledger_account,
    credit_account_id=reserved_ledger_account,
            amount=amount,
            reference=reference,
            description="Escrow Release"
        )

        await self.audit.log(
            db=db,
            user_id="system",
            action="escrow_release",
            entity_type="escrow",
            entity_id=escrow.id,
            reference=reference,
            amount=float(amount),
            metadata={"amount": str(amount)}
        )

        await outbox_service.queue_event(
            db=db,
            topic="financial.escrow.release",
            payload={
                "escrow_id": escrow.id,
                "amount": str(amount),
                "reference": reference
            }
        )

        return escrow

    # =========================================================
    # WALLET → WALLET TRANSFER (SAFE INTERNAL MOVEMENT)
    # =========================================================
    async def transfer(
        self,
        db: AsyncSession,
        from_wallet_id: str,
        to_wallet_id: str,
        amount: Decimal,
        reference: str
        receiver_ledger_account: str,
        sender_ledger_account: str
    ):

        await self._ensure_idempotent(
            db,
            reference
        )
      
        if amount <= 0:
            raise HTTPException(
                400,
                "Invalid amount"
            )

        sender = await self._lock_wallet(db, from_wallet_id)
        receiver = await self._lock_wallet(db, to_wallet_id)

        if sender.balance < amount:
            raise HTTPException(400, "Insufficient balance")

        sender.balance -= amount
        receiver.balance += amount

        sender.version += 1
        receiver.version += 1

        await self._post_double_entry(
            db=db,
    debit_account_id=receiver_ledger_account,
    credit_account_id=sender_ledger_account,
            amount=amount,
            reference=reference,
            description="Wallet Transfer"
        )

        await outbox_service.queue_event(
            db=db,
            topic="financial.wallet.transfer",
            payload={
                "from": sender.id,
                "to": receiver.id,
                "amount": str(amount),
                "reference": reference
            }
        )

        return sender, receiver

    # =========================================================
    # ATOMIC COMMIT SAFETY BOUNDARY
    # =========================================================
    async def commit(self, db:   
    AsyncSession):
        try:
            await db.commit()

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Transaction    failed: {str(e)}"
            )

    # =========================================================
# IDEMPOTENCY
# =========================================================

    async def _ensure_idempotent(
        self,
        db: AsyncSession,
        reference: str
    ):
        exists = await     idempotency_service.exists(
            db=db,
            key=reference
        )

        if exists:
            raise HTTPException(
                status_code=409,
                detail="Reference already  processed"
            )

        await idempotency_service.record(
            db=db,
            key=reference
        )


    # =========================================================
# LEDGER SAFETY
# =========================================================

    async def _post_double_entry(
        self,
        db: AsyncSession,
        debit_account_id: str,
        credit_account_id: str,
        amount: Decimal,
        reference: str,
        description: str | None = None
    ):
        if amount <= 0:
            raise HTTPException(400,    
    "Invalid amount")

    # =========================================================
    # VALIDATE LEDGER ACCOUNTS EXIST (CRITICAL FIX)
    # =========================================================
        debit_account = await       self._lock_ledger(db, debit_account_id)
        credit_account = await self._lock_ledger(db, credit_account_id)

        if not debit_account:
            raise HTTPException(
                status_code=404,
                detail=f"Debit ledger              
    account not found: {debit_account_id}"
            )

        if not credit_account:
            raise HTTPException(
                status_code=404,
                detail=f"Credit ledger     
    account not found: {credit_account_id}"
            )

    # =========================================================
    # CREATE DOUBLE ENTRY
    # =========================================================
        debit = LedgerEntry(
            account_id=debit_account_id,
            entry_type="debit",
            amount=amount,
            transaction_reference=reference,
            description=description
        )

        credit = LedgerEntry(
            account_id=credit_account_id,
            entry_type="credit",
            amount=amount,
            transaction_reference=reference,
            description=description
        )

        db.add_all([debit, credit])

        return debit, credit
    # =========================================================
    # WALLET CREDIT (POST-PAYMENT SETTLEMENT)
    # ========================================================

    async def wallet_credit(
        self,
        db: AsyncSession,
        wallet_id: str,
        amount: Decimal,
        reference: str,
        debit_ledger_account: str,
        credit_ledger_account: str
    ):
        await self._ensure_idempotent(
            db,
            reference
        )
        
        if amount <= 0:
            raise HTTPException(
                400,
                "Invalid amount"
            )

        wallet = await self._lock_wallet(
            db,
            wallet_id
        )

        wallet.balance += amount
        wallet.version += 1

        await self._post_double_entry(
            db=db,
          
    debit_account_id=debit_ledger_account,
          credit_account_id=credit_ledger_account,
            amount=amount,
            reference=reference,
            description="Wallet Credit"
        )

        await self.audit.log(
            db=db,
            user_id=wallet.user_id,
            action="wallet_credit",
            entity_type="wallet",
            entity_id=wallet.id,
            reference=reference,
            amount=float(amount)
        )

        await outbox_service.queue_event(
            db=db,
          topic="financial.wallet.credit",
            payload={
                "wallet_id": wallet.id,
                "amount": str(amount),
                "reference": reference
            }
        )

        return wallet

# =========================================================
    # ESCROW DEPOSIT (PAYMENT GATEWAY → ESCROW ONLY)
    # =========================================================
      


    async def escrow_deposit(
        self,
        db: AsyncSession,
        escrow_id: str,
        amount: Decimal,
        reference: str,
        debit_ledger_account: str,
        credit_ledger_account: str
    ):
        await self._ensure_idempotent(
            db,
            reference
        )

        if amount <= 0:
            raise HTTPException(
                400,
                "Invalid amount"
            )

        escrow = await self._lock_escrow(
            db,
            escrow_id
        )

        if escrow.is_frozen:
            raise HTTPException(
                400,
                "Escrow frozen"
            )

        escrow.total_deposited += amount
        escrow.available_balance += amount
        escrow.ledger_balance += amount
        escrow.version += 1

        await self._post_double_entry(
            db=db,
         debit_account_id=debit_ledger_account,
         credit_account_id=credit_ledger_account,
            amount=amount,
            reference=reference,
            description="Escrow Deposit"
        )

        await self.audit.log(
            db=db,
            user_id="system",
            action="escrow_deposit",
            entity_type="escrow",
            entity_id=escrow.id,
            reference=reference,
            amount=float(amount)
        )

        await outbox_service.queue_event(
            db=db,
            topic="financial.escrow.deposit",
            payload={
                "escrow_id": escrow.id,
                "amount": str(amount),
                "reference": reference
            }
        )

        return escrow


