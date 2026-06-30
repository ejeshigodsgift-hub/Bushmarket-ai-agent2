from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.ledger_account import LedgerAccount

from app.db.models.wallet import Wallet
from app.db.models.payment_intent import PaymentIntent
from app.db.models.payment_transaction import PaymentTransaction
from app.db.models.ledger_account import LedgerAccount

from app.services.financial_core_service import FinancialCoreService
from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from app.services.idempotency_service import idempotency_service


class WalletService:
    """
    WALLET DOMAIN SERVICE
    Handles wallet lifecycle + orchestrates financial core
    """

    def __init__(self):
        self.financial_core = FinancialCoreService()
        self.audit = AuditService()

    # =====================================================
    # WALLET CREATION
    # =====================================================
    async def create_wallet(
        self,
        db: AsyncSession,
        user_id: str,
        currency: str = "NGN"
    ):
        existing = await db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )

        if existing.scalar_one_or_none():
            raise HTTPException(400, "Wallet already exists")

        wallet = Wallet(
            user_id=user_id,
            balance=Decimal("0.00"),
            currency=currency
        )

        db.add(wallet)


        await db.flush()

        existing_ledger = await db.execute(
            select(LedgerAccount).where(
                LedgerAccount.user_id == user_id,
                LedgerAccount.account_type == "wallet"
            )
        )

        if not  existing_ledger.scalar_one_or_none():

            db.add(
                LedgerAccount(
                    user_id=user_id,
                    account_type="wallet",
                    currency=currency,
                    is_active=True
                )
            )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="wallet_created",
            entity_type="wallet",
            entity_id=wallet.id,
            reference=wallet.id
        )

        await outbox_service.queue_event(
            db=db,
            topic="wallet.created",
            payload={
                "wallet_id": wallet.id,
                "user_id": user_id
            }
        )

        return wallet

    # =====================================================
    # WALLET LOOKUP
    # =====================================================
    async def get_wallet(
        self,
        db: AsyncSession,
        wallet_id: str
    ):
        stmt = select(Wallet).where(Wallet.id == wallet_id)
        result = await db.execute(stmt)

        wallet = result.scalar_one_or_none()

        if not wallet:
            raise HTTPException(404, "Wallet not found")

        return wallet

    # =====================================================
    # BALANCE QUERY
    # =====================================================
    async def get_balance(
        self,
        db: AsyncSession,
        wallet_id: str
    ):
        wallet = await self.get_wallet(db, wallet_id)
        return {
            "wallet_id": wallet.id,
            "balance": str(wallet.balance),
            "currency": wallet.currency
        }

    # =====================================================
    # WALLET TOP-UP (ENTRY POINT)
    # =====================================================
    async def topup_wallet(
        self,
        db: AsyncSession,
        user_id: str,
        wallet_id: str,
        amount: Decimal,
        reference: str,
        ledger_credit_account: str,
        ledger_debit_account: str
    ):
        """
        Called AFTER payment webhook success
        Gateway → Escrow → Wallet Credit
        """

        await idempotency_service.ensure(
            db=db,
            key=reference
        )

        if amount <= 0:
            raise HTTPException(400, "Invalid amount")

        wallet = await self.get_wallet(db, wallet_id)

        # 1. CREDIT WALLET (SOURCE OF TRUTH UPDATE)
        wallet.balance += amount
        wallet.version += 1

        # 2. LEDGER POSTING (MANDATORY DOUBLE ENTRY)
        await self.financial_core._post_double_entry(
            db=db,
            debit_account_id=ledger_debit_account,
            credit_account_id=ledger_credit_account,
            amount=amount,
            reference=reference,
            description="Wallet Top-up"
        )

        # 3. AUDIT LOG
        await self.audit.log(
            db=db,
            user_id=user_id,
            action="wallet_topup",
            entity_type="wallet",
            entity_id=wallet.id,
            reference=reference,
            amount=float(amount),
            metadata={"amount": str(amount)}
        )

        # 4. OUTBOX EVENT
        await outbox_service.queue_event(
            db=db,
            topic="wallet.topup.completed",
            payload={
                "wallet_id": wallet.id,
                "user_id": user_id,
                "amount": str(amount),
                "reference": reference
            }
        )

        return wallet

    # =====================================================
    # WALLET WITHDRAWAL (PREPARATION PHASE)
    # =====================================================
    async def request_withdrawal(
        self,
        db: AsyncSession,
        wallet_id: str,
        amount: Decimal,
        reference: str
    ):
        """
        Creates withdrawal request (actual payout handled separately)
        """

        await idempotency_service.ensure(db=db, key=reference)

        wallet = await self.get_wallet(db, wallet_id)

        if wallet.balance < amount:
            raise HTTPException(400, "Insufficient balance")

        # Reserve funds (not yet deducted permanently)
        wallet.balance -= amount
        wallet.version += 1

        await self.audit.log(
            db=db,
            user_id=wallet.user_id,
            action="wallet_withdrawal_requested",
            entity_type="wallet",
            entity_id=wallet.id,
            reference=reference,
            amount=float(amount)
        )

        await outbox_service.queue_event(
            db=db,
            topic="wallet.withdrawal.requested",
            payload={
                "wallet_id": wallet.id,
                "amount": str(amount),
                "reference": reference
            }
        )

        return wallet