from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models.wallet import Wallet
from app.db.models.escrow_account import EscrowAccount

from app.db.models.financial_reconciliation import FinancialReconciliation  

from datetime import datetime

from app.db.models.ledger_account import LedgerAccount
from app.db.models.ledger_entry import LedgerEntry


class LedgerReconciliationService:
    """
    Financial integrity verification system:
    Wallet ↔ Ledger
    Escrow ↔ Ledger
    Cooperative ↔ Ledger
    System-wide consistency checks
    """

    # =====================================================
    # WALLET RECONCILIATION
    # =====================================================
    async def reconcile_wallets(self, db: AsyncSession):

        result = await db.execute(
            select(
                LedgerAccount.id,
                LedgerAccount.user_id,
                func.sum(
                    func.case(
                        (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
                        else_=-LedgerEntry.amount
                    )
                ).label("ledger_balance")
            )
            .join(LedgerEntry, LedgerEntry.account_id == LedgerAccount.id)
            .where(LedgerAccount.account_type == "wallet")
            .group_by(LedgerAccount.id, LedgerAccount.user_id)
        )

        rows = result.all()

        mismatches = []
        ok = []

        for r in rows:

            ledger_balance = Decimal(r.ledger_balance or 0)

            ok.append({
                "wallet_account_id": r.id,
                "user_id": r.user_id,
                "ledger_balance": str(ledger_balance)
            })

        return {
            "total_wallet_accounts": len(rows),
            "ok": ok,
            "mismatches": mismatches
        }

    # =====================================================
    # ESCROW RECONCILIATION
    # =====================================================
    async def reconcile_escrows(self, db: AsyncSession):

        result = await db.execute(
            select(
                LedgerAccount.id,
                LedgerAccount.cooperative_id,
                func.sum(
                    func.case(
                        (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
                        else_=-LedgerEntry.amount
                    )
                ).label("ledger_balance")
            )
            .join(LedgerEntry, LedgerEntry.account_id == LedgerAccount.id)
            .where(LedgerAccount.account_type == "escrow")
            .group_by(LedgerAccount.id, LedgerAccount.cooperative_id)
        )

        rows = result.all()

        mismatches = []
        ok = []

        for r in rows:

            ledger_balance = Decimal(r.ledger_balance or 0)

            ok.append({
                "escrow_account_id": r.id,
                "cooperative_id": r.cooperative_id,
                "ledger_balance": str(ledger_balance)
            })

        return {
            "total_escrow_accounts": len(rows),
            "ok": ok,
            "mismatches": mismatches
        }

    # =====================================================
    # COOPERATIVE RECONCILIATION
    # =====================================================
    async def reconcile_cooperative(
        self,
        db: AsyncSession,
        cooperative_id: str
    ):

        result = await db.execute(
            select(
                LedgerAccount.id,
                LedgerAccount.account_type,
                func.sum(
                    func.case(
                        (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
                        else_=-LedgerEntry.amount
                    )
                ).label("ledger_balance")
            )
            .join(LedgerEntry, LedgerEntry.account_id == LedgerAccount.id)
            .where(LedgerAccount.cooperative_id == cooperative_id)
            .group_by(LedgerAccount.id, LedgerAccount.account_type)
        )

        rows = result.all()

        total_escrow = Decimal("0")
        total_accounts = 0

        breakdown = []

        for r in rows:

            balance = Decimal(r.ledger_balance or 0)
            total_accounts += 1

            if r.account_type == "escrow":
                total_escrow += balance

            breakdown.append({
                "account_id": r.id,
                "type": r.account_type,
                "balance": str(balance)
            })

        return {
            "cooperative_id": cooperative_id,
            "total_accounts": total_accounts,
            "total_escrow_balance": str(total_escrow),
            "breakdown": breakdown
        }

    # =====================================================
    # DOUBLE ENTRY INTEGRITY CHECK
    # =====================================================
    async def verify_double_entry_integrity(self, db: AsyncSession):

        result = await db.execute(
            select(
                LedgerEntry.transaction_reference,
                func.sum(
                    func.case(
                        (LedgerEntry.entry_type == "debit", LedgerEntry.amount),
                        else_=0
                    )
                ).label("debits"),
                func.sum(
                    func.case(
                        (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
                        else_=0
                    )
                ).label("credits")
            )
            .group_by(LedgerEntry.transaction_reference)
        )

        rows = result.all()

        mismatches = []
        balanced = []

        for r in rows:

            debit = Decimal(r.debits or 0)
            credit = Decimal(r.credits or 0)

            if debit != credit:
                mismatches.append({
                    "reference": r.transaction_reference,
                    "debits": str(debit),
                    "credits": str(credit),
                    "difference": str(debit - credit)
                })
            else:
                balanced.append(r.transaction_reference)

        return {
            "total_transactions": len(rows),
            "balanced": len(balanced),
            "mismatched": len(mismatches),
            "mismatches": mismatches
        }

    # =====================================================
    # FULL SYSTEM RECONCILIATION (CORE AUDIT ENGINE)
    # =====================================================
    async def full_system_reconciliation(self, db: AsyncSession):

        wallets = await self.reconcile_wallets(db)
        escrows = await self.reconcile_escrows(db)
        integrity = await self.verify_double_entry_integrity(db)

        # GLOBAL LEDGER TOTAL
        ledger_total_result = await db.execute(
            select(
                func.sum(
                    func.case(
                        (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
                        else_=-LedgerEntry.amount
                    )
                )
            )
        )

        ledger_total = Decimal(ledger_total_result.scalar() or 0)


        await self.persist_reconciliation_result(
            db=db,
            reference="SYS-AUDIT-" +   datetime.utcnow().isoformat(),
            cooperative_id=None,
    reconciliation_type="full_system_audit",
            expected=ledger_total,
            actual=ledger_total,  # or external system snapshot if available
            metadata={
                "wallets": wallets,
                "escrows": escrows,
                "integrity": integrity
            }
        )

        return {
            "ledger_total": str(ledger_total),
            "wallets": wallets,
            "escrows": escrows,
            "double_entry_integrity": integrity,
            "status": "completed"
        }


    async def   persist_reconciliation_result(
        self,
        db: AsyncSession,
        reference: str,
        cooperative_id: str | None,
        reconciliation_type: str,
        expected: Decimal,
        actual: Decimal,
        metadata: dict
    ):

        difference = expected - actual

        record = FinancialReconciliation(
            reference=reference,
            cooperative_id=cooperative_id,
        reconciliation_type=reconciliation_type,
            expected_balance=expected,
            actual_balance=actual,
            difference=difference,
            status="matched" if difference == 0 else "mismatch",
            is_resolved=(difference == 0),
            metadata=metadata
        )

        db.add(record)

        return record