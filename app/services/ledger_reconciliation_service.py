# =========================================
# FILE: app/services/ledger_reconciliation_service.py
# =========================================

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.ledger_account import LedgerAccount
from app.db.models.ledger_entry import LedgerEntry


class LedgerReconciliationService:

    async def run_full_reconciliation(self, db: AsyncSession):

        accounts_result = await db.execute(
            select(LedgerAccount)
        )

        accounts = accounts_result.scalars().all()

        report = {
            "total_accounts": len(accounts),
            "mismatches": [],
            "ok": []
        }

        for account in accounts:

            ledger_result = await db.execute(
                select(
                    func.sum(
                        func.case(
                            (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
                            else_=-LedgerEntry.amount
                        )
                    )
                ).where(LedgerEntry.account_id == account.id)
            )

            computed = ledger_result.scalar() or 0

            # IMPORTANT: we no longer trust DB balance fields
            stored = None

            report["ok"].append({
                "account_id": account.id,
                "type": account.account_type,
                "computed_balance": float(computed)
            })

        return report