import json
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.financial_transaction import (
    FinancialTransaction
)


class FinancialTransactionService:
    """
    Central immutable financial transaction writer.

    Every financial operation should create
    exactly one FinancialTransaction record.
    """

    async def create_transaction(
        self,
        db: AsyncSession,
        reference: str,
        transaction_type: str,
        amount: Decimal,

        wallet_id: str | None = None,
        escrow_account_id: str | None = None,

        payment_intent_id: str | None = None,
        payment_transaction_id: str | None = None,

        debit_ledger_account_id: str | None = None,
        credit_ledger_account_id: str | None = None,

        status: str = "completed",
        currency: str = "NGN",

        created_by: str | None = None,
        metadata: dict | None = None
    ) -> FinancialTransaction:

        tx = FinancialTransaction(
            reference=reference,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,

            wallet_id=wallet_id,
            escrow_account_id=escrow_account_id,

            payment_intent_id=payment_intent_id,
            payment_transaction_id=payment_transaction_id,

            debit_ledger_account_id=debit_ledger_account_id,
            credit_ledger_account_id=credit_ledger_account_id,

            status=status,
            created_by=created_by,

            metadata=(
                json.dumps(metadata)
                if metadata
                else None
            )
        )

        db.add(tx)

        await db.flush()

        return tx

    async def wallet_credit(
        self,
        db: AsyncSession,
        wallet_id: str,
        amount: Decimal,
        reference: str,
        debit_ledger_account_id: str,
        credit_ledger_account_id: str,
        created_by: str | None = None
    ):
        return await self.create_transaction(
            db=db,
            reference=reference,
            transaction_type="wallet_credit",
            amount=amount,
            wallet_id=wallet_id,
            debit_ledger_account_id=debit_ledger_account_id,
            credit_ledger_account_id=credit_ledger_account_id,
            created_by=created_by
        )

    async def wallet_debit(
        self,
        db: AsyncSession,
        wallet_id: str,
        amount: Decimal,
        reference: str,
        debit_ledger_account_id: str,
        credit_ledger_account_id: str,
        created_by: str | None = None
    ):
        return await self.create_transaction(
            db=db,
            reference=reference,
            transaction_type="wallet_debit",
            amount=amount,
            wallet_id=wallet_id,
            debit_ledger_account_id=debit_ledger_account_id,
            credit_ledger_account_id=credit_ledger_account_id,
            created_by=created_by
        )

    async def wallet_transfer(
        self,
        db: AsyncSession,
        wallet_id: str,
        amount: Decimal,
        reference: str,
        debit_ledger_account_id: str,
        credit_ledger_account_id: str
    ):
        return await self.create_transaction(
            db=db,
            reference=reference,
            transaction_type="wallet_transfer",
            amount=amount,
            wallet_id=wallet_id,
            debit_ledger_account_id=debit_ledger_account_id,
            credit_ledger_account_id=credit_ledger_account_id
        )


    async def withdrawal(
        self,
        db: AsyncSession,
        wallet_id: str,
        amount: Decimal,
        reference: str,
        debit_ledger_account_id: str,
        credit_ledger_account_id: str,
        created_by: str | None = None
    ):
        return await self.create_transaction(
            db=db,
            reference=reference,
            transaction_type="withdrawal",
            amount=amount,
            wallet_id=wallet_id,
        debit_ledger_account_id=debit_ledger_account_id,
        credit_ledger_account_id=credit_ledger_account_id,
            created_by=created_by
        )



    async def escrow_deposit(
        self,
        db: AsyncSession,
        escrow_account_id: str,
        amount: Decimal,
        reference: str,
        debit_ledger_account_id: str,
        credit_ledger_account_id: str
    ):
        return await self.create_transaction(
            db=db,
            reference=reference,
            transaction_type="escrow_deposit",
            amount=amount,
            escrow_account_id=escrow_account_id,
            debit_ledger_account_id=debit_ledger_account_id,
            credit_ledger_account_id=credit_ledger_account_id
        )

    async def escrow_hold(
        self,
        db: AsyncSession,
        escrow_account_id: str,
        amount: Decimal,
        reference: str,
        debit_ledger_account_id: str,
        credit_ledger_account_id: str
    ):
        return await self.create_transaction(
            db=db,
            reference=reference,
            transaction_type="escrow_hold",
            amount=amount,
            escrow_account_id=escrow_account_id,
            debit_ledger_account_id=debit_ledger_account_id,
            credit_ledger_account_id=credit_ledger_account_id
        )


    


    async def escrow_release(
        self,
        db: AsyncSession,
        escrow_account_id: str,
        amount: Decimal,
        reference: str,
        debit_ledger_account_id: str,
        credit_ledger_account_id: str
    ):
        return await self.create_transaction(
            db=db,
            reference=reference,
            transaction_type="escrow_release",
            amount=amount,
            escrow_account_id=escrow_account_id,
            debit_ledger_account_id=debit_ledger_account_id,
            credit_ledger_account_id=credit_ledger_account_id
        )

    async def refund(
        self,
        db: AsyncSession,
        amount: Decimal,
        reference: str,
        wallet_id: str | None = None,
        escrow_account_id: str | None = None
    ):
        return await self.create_transaction(
            db=db,
            reference=reference,
            transaction_type="refund",
            amount=amount,
            wallet_id=wallet_id,
            escrow_account_id=escrow_account_id
        )


financial_transaction_service = (
    FinancialTransactionService()
)