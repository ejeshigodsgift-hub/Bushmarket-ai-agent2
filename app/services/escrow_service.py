# =========================================
# FILE: app/services/escrow_service.py
# =========================================

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.escrow_account import EscrowAccount
from app.db.models.escrow_transaction import EscrowTransaction

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service


class EscrowService:

    def __init__(self):
        self.audit = AuditService()

    # =========================================
    # CREATE ESCROW ACCOUNT
    # =========================================
    async def create_escrow_account(
        self,
        db: AsyncSession,
        cooperative_id: str
    ):

         # I DISABLED CODE WITH RETURN NONE

        return None 

        result = await db.execute(
            select(EscrowAccount).where(
                EscrowAccount.cooperative_id == cooperative_id
            )
        )

        existing = result.scalar_one_or_none()

        if existing:
            return existing

        escrow = EscrowAccount(
            cooperative_id=cooperative_id,
            total_deposited=0,
            total_reserved=0,
            available_balance=0,
            status="active",
            is_frozen=False
        )

        db.add(escrow)
        await db.flush()

        await outbox_service.queue_event(
            db=db,
            topic="escrow.created",
            payload={
                "escrow_account_id": escrow.id,
                "cooperative_id": cooperative_id
            }
        )

        return escrow

    # =========================================
    # DEPOSIT (FROM PAYMENT CORE → ESCROW)
    # =========================================
    async def deposit(
        self,
        db: AsyncSession,
        escrow_account_id: str,
        amount: float,
        reference: str,
        meta: dict | None = None
    ):

          # I DISABLED CODE WITH RETURN NONE

        return None       

        escrow = await db.get(EscrowAccount, escrow_account_id)

        if not escrow:
            raise HTTPException(404, "Escrow account not found")

        if escrow.is_frozen:
            raise HTTPException(400, "Escrow is frozen")

        escrow.total_deposited += amount
        escrow.available_balance += amount

        tx = EscrowTransaction(
            escrow_account_id=escrow.id,
            transaction_type="deposit",
            amount=amount,
            reference=reference,
            metadata=meta or {}
        )

        db.add(tx)

        await self.audit.log(
            db=db,
            user_id="system",
            action="escrow_deposit",
            entity_type="escrow_account",
            entity_id=escrow.id,
            metadata={"amount": amount, "reference": reference}
        )

        await outbox_service.queue_event(
            db=db,
            topic="escrow.deposit",
            payload={
                "escrow_account_id": escrow.id,
                "amount": amount,
                "reference": reference
            }
        )

        await db.commit()
        await db.refresh(escrow)

        return escrow

    # =========================================
    # RELEASE FUNDS (TO PLATFORM OR SUPPLIER LATER)
    # =========================================
    async def release(
        self,
        db: AsyncSession,
        escrow_account_id: str,
        amount: float,
        reference: str
    ):

         # I DISABLED CODE WITH RETURN NONE

        return None 

        escrow = await db.get(EscrowAccount, escrow_account_id)

        if escrow.available_balance < amount:
            raise HTTPException(400, "Insufficient escrow balance")

        escrow.available_balance -= amount
        escrow.total_reserved += amount

        tx = EscrowTransaction(
            escrow_account_id=escrow.id,
            transaction_type="release",
            amount=amount,
            reference=reference
        )

        db.add(tx)

        await outbox_service.queue_event(
            db=db,
            topic="escrow.release",
            payload={
                "escrow_account_id": escrow.id,
                "amount": amount,
                "reference": reference
            }
        )

        await db.commit()

        return escrow

    # =========================================
    # REFUND
    # =========================================
    async def refund(
        self,
        db: AsyncSession,
        escrow_account_id: str,
        amount: float,
        reference: str
    ):

         # I DISABLED CODE WITH RETURN NONE

        return None 

        escrow = await db.get(EscrowAccount, escrow_account_id)

        if escrow.total_deposited < amount:
            raise HTTPException(400, "Invalid refund amount")

        escrow.total_deposited -= amount
        escrow.available_balance -= amount

        tx = EscrowTransaction(
            escrow_account_id=escrow.id,
            transaction_type="refund",
            amount=amount,
            reference=reference
        )

        db.add(tx)

        await outbox_service.queue_event(
            db=db,
            topic="escrow.refund",
            payload={
                "escrow_account_id": escrow.id,
                "amount": amount,
                "reference": reference
            }
        )

        await db.commit()

        return escrow


escrow_service = EscrowService()