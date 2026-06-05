from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ledger_entry import LedgerEntry
from app.db.models.ledger_account import LedgerAccount


class LedgerProjectionService:

    async def account_balance(
        self,
        db: AsyncSession,
        account_id: str
    ) -> Decimal:

        debit_query = (
            select(func.coalesce(func.sum(LedgerEntry.amount), 0))
            .where(
                LedgerEntry.account_id == account_id,
                LedgerEntry.entry_type == "debit"
            )
        )

        credit_query = (
            select(func.coalesce(func.sum(LedgerEntry.amount), 0))
            .where(
                LedgerEntry.account_id == account_id,
                LedgerEntry.entry_type == "credit"
            )
        )

        debit_total = (await db.execute(debit_query)).scalar() or Decimal("0")
        credit_total = (await db.execute(credit_query)).scalar() or Decimal("0")

        return debit_total - credit_total

    async def project_balance(
        self,
        db: AsyncSession,
        account_id: str,
        incoming: Decimal = Decimal("0"),
        outgoing: Decimal = Decimal("0")
    ):

        current = await self.account_balance(
            db,
            account_id
        )

        return current + incoming - outgoing

    async def all_balances(
        self,
        db: AsyncSession
    ):

        result = await db.execute(
            select(LedgerAccount)
        )

        accounts = result.scalars().all()

        balances = []

        for account in accounts:

            balance = await self.account_balance(
                db,
                account.id
            )

            balances.append({
                "account_id": account.id,
                "account_type": account.account_type,
                "currency": account.currency,
                "balance": str(balance)
            })

        return balances

    async def verify_double_entry(
        self,
        db: AsyncSession,
        transaction_reference: str
    ):

        result = await db.execute(
            select(LedgerEntry)
            .where(
                LedgerEntry.transaction_reference
                == transaction_reference
            )
        )

        entries = result.scalars().all()

        debit_total = Decimal("0")
        credit_total = Decimal("0")

        for entry in entries:

            if entry.entry_type == "debit":
                debit_total += entry.amount

            if entry.entry_type == "credit":
                credit_total += entry.amount

        return {
            "balanced": debit_total == credit_total,
            "debits": str(debit_total),
            "credits": str(credit_total)
        }