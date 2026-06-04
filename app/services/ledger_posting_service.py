from decimal import Decimalfrom sqlalchemy.ext.asyncio import AsyncSessionfrom sqlalchemy import select

from app.db.models.ledger_account import LedgerAccountfrom app.db.models.ledger_entry import LedgerEntry

class LedgerPostingService:

async def post_double_entry(
    self,
    db: AsyncSession,
    debit_account_id: str,
    credit_account_id: str,
    amount: Decimal,
    reference: str,
    description: str | None = None
):

    debit = LedgerEntry(
        account_id=debit_account_id,
        transaction_reference=reference,
        entry_type="debit",
        amount=amount,
        description=description
    )

    credit = LedgerEntry(
        account_id=credit_account_id,
        transaction_reference=reference,
        entry_type="credit",
        amount=amount,
        description=description
    )

    db.add(debit)
    db.add(credit)

    await db.flush()

    return {
        "reference": reference,
        "amount": float(amount)
    }

ledger_posting_service = LedgerPostingService()