from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy import select, func

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ledger_entry import LedgerEntry
from app.db.models.wallet import Wallet
from app.db.models.escrow_account import EscrowAccount
from app.db.models.order import Order
from app.db.models.payment_transaction import PaymentTransaction


class FinancialReportingService:

    def _period_start(self, period: str):

        now = datetime.utcnow()

        if period == "daily":
            return now - timedelta(days=1)

        if period == "weekly":
            return now - timedelta(days=7)

        if period == "monthly":
            return now - timedelta(days=30)

        if period == "yearly":
            return now - timedelta(days=365)

        raise ValueError("Invalid period")

    async def transaction_volume(
        self,
        db: AsyncSession,
        period: str
    ):

        start = self._period_start(period)

        result = await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        PaymentTransaction.amount
                    ),
                    0
                )
            ).where(
                PaymentTransaction.created_at >= start
            )
        )

        total = result.scalar()

        return {
            "period": period,
            "transaction_volume": str(total)
        }

    async def order_volume(
        self,
        db: AsyncSession,
        period: str
    ):

        start = self._period_start(period)

        result = await db.execute(
            select(
                func.coalesce(
                    func.sum(Order.total_amount),
                    0
                )
            ).where(
                Order.created_at >= start
            )
        )

        return {
            "period": period,
            "order_volume": str(result.scalar())
        }

    async def escrow_summary(
        self,
        db: AsyncSession
    ):

        total_escrow = await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        EscrowAccount.ledger_balance
                    ),
                    0
                )
            )
        )

        total_reserved = await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        EscrowAccount.total_reserved
                    ),
                    0
                )
            )
        )

        return {
            "ledger_balance":
                str(total_escrow.scalar()),
            "reserved":
                str(total_reserved.scalar())
        }

    async def wallet_summary(
        self,
        db: AsyncSession
    ):

        total_wallets = await db.execute(
            select(
                func.coalesce(
                    func.sum(Wallet.balance),
                    0
                )
            )
        )

        return {
            "wallet_balance":
                str(total_wallets.scalar())
        }

    async def ledger_summary(
        self,
        db: AsyncSession,
        period: str
    ):

        start = self._period_start(period)

        debit_total = await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        LedgerEntry.amount
                    ),
                    0
                )
            ).where(
                LedgerEntry.entry_type == "debit",
                LedgerEntry.created_at >= start
            )
        )

        credit_total = await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        LedgerEntry.amount
                    ),
                    0
                )
            ).where(
                LedgerEntry.entry_type == "credit",
                LedgerEntry.created_at >= start
            )
        )

        return {
            "period": period,
            "debits":
                str(debit_total.scalar()),
            "credits":
                str(credit_total.scalar())
        }

    async def platform_report(
        self,
        db: AsyncSession,
        period: str
    ):

        return {
            "transactions":
                await self.transaction_volume(
                    db,
                    period
                ),

            "orders":
                await self.order_volume(
                    db,
                    period
                ),

            "wallets":
                await self.wallet_summary(
                    db
                ),

            "escrow":
                await self.escrow_summary(
                    db
                ),

            "ledger":
                await self.ledger_summary(
                    db,
                    period
                )
        }