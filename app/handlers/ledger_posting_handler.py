from decimal import Decimal

from app.services.ledger_posting_service import (ledger_posting_service)

class LedgerPostingHandler:

async def handle(self, db, event):

    amount = Decimal(
        str(event.get("amount", 0))
    )

    debit_account_id = event.get(
        "debit_account_id"
    )

    credit_account_id = event.get(
        "credit_account_id"
    )

    reference = event.get("reference")

    if not (
        debit_account_id and
        credit_account_id and
        reference
    ):
        return

    await ledger_posting_service.post_double_entry(
        db=db,
        debit_account_id=debit_account_id,
        credit_account_id=credit_account_id,
        amount=amount,
        reference=reference,
        description=event.get("description")
    )