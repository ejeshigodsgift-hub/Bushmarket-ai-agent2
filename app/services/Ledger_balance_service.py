# =========================================
# FILE: app/services/ledger_balance_service.py
# =========================================

from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ledger_entry import LedgerEntry
from app.db.models.ledger_account import LedgerAccount


class LedgerBalanceService:

    # ================================
    # WALLET BALANCE (SOURCE OF TRUTH)
    # ================================
    async def get_wallet_balance(
        self,
        db: AsyncSession,
        user_id: str,
        currency: str = "NGN"
    ) -> Decimal:

        result = await db.execute(
            select(
                func.sum(
                    func.case(
                        (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
                        else_=-LedgerEntry.amount
                    )
                )
            )
            .join(LedgerAccount, LedgerAccount.id == LedgerEntry.account_id)
            .where(
                LedgerAccount.user_id == user_id,
                LedgerAccount.account_type == "wallet",
                LedgerAccount.currency == currency
            )
        )

        balance = result.scalar() or Decimal("0.00")
        return Decimal(balance)

    # ================================
    # ESCROW BALANCE (SOURCE OF TRUTH)
    # ================================
    async def get_escrow_balance(
        self,
        db: AsyncSession,
        cooperative_id: str,
        currency: str = "NGN"
    ) -> Decimal:

        result = await db.execute(
            select(
                func.sum(
                    func.case(
                        (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
                        else_=-LedgerEntry.amount
                    )
                )
            )
            .join(LedgerAccount, LedgerAccount.id == LedgerEntry.account_id)
            .where(
                LedgerAccount.cooperative_id == cooperative_id,
                LedgerAccount.account_type == "escrow",
                LedgerAccount.currency == currency
            )
        )

        balance = result.scalar() or Decimal("0.00")
        return Decimal(balance)

    # ================================
    # PLATFORM BALANCE (OPTIONAL)
    # ================================
    async def get_platform_balance(
        self,
        db: AsyncSession,
        currency: str = "NGN"
    ) -> Decimal:

        result = await db.execute(
            select(
                func.sum(
                    func.case(
                        (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
                        else_=-LedgerEntry.amount
                    )
                )
            )
            .join(LedgerAccount, LedgerAccount.id == LedgerEntry.account_id)
            .where(
                LedgerAccount.account_type == "platform",
                LedgerAccount.currency == currency
            )
        )

        return Decimal(result.scalar() or 0)

    # ================================
    # FULL ACCOUNT RECONCILIATION
    # ================================
    async def reconcile_account(
        self,
        db: AsyncSession,
        account_id: str
    ):

        result = await db.execute(
            select(
                func.sum(
                    func.case(
                        (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
                        else_=-LedgerEntry.amount
                    )
                )
            )
            .where(LedgerEntry.account_id == account_id)
        )

        computed_balance = Decimal(result.scalar() or 0)

        account = await db.get(LedgerAccount, account_id)

        return {
            "account_id": account_id,
            "account_type": account.account_type,
            "stored_balance": None,  # deprecated (we stop trusting this)
            "computed_balance": computed_balance,
            "is_consistent": True
        }