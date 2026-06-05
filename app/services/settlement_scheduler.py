from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.escrow_account import EscrowAccount
from app.services.financial_core_service import FinancialCoreService


class SettlementScheduler:

    def __init__(self):
        self.financial = FinancialCoreService()

    # =========================================
    # T+1
    # =========================================

    async def process_t1(
        self,
        db: AsyncSession,
        settlement_account_id: str,
        reserved_account_id: str
    ):

        return await self._process(
            db=db,
            age_days=1,
            settlement_account_id=settlement_account_id,
            reserved_account_id=reserved_account_id
        )

    # =========================================
    # T+3
    # =========================================

    async def process_t3(
        self,
        db: AsyncSession,
        settlement_account_id: str,
        reserved_account_id: str
    ):

        return await self._process(
            db=db,
            age_days=3,
            settlement_account_id=settlement_account_id,
            reserved_account_id=reserved_account_id
        )

    # =========================================
    # WEEKLY
    # =========================================

    async def process_weekly(
        self,
        db: AsyncSession,
        settlement_account_id: str,
        reserved_account_id: str
    ):

        return await self._process(
            db=db,
            age_days=7,
            settlement_account_id=settlement_account_id,
            reserved_account_id=reserved_account_id
        )

    # =========================================
    # MONTHLY
    # =========================================

    async def process_monthly(
        self,
        db: AsyncSession,
        settlement_account_id: str,
        reserved_account_id: str
    ):

        return await self._process(
            db=db,
            age_days=30,
            settlement_account_id=settlement_account_id,
            reserved_account_id=reserved_account_id
        )

    # =========================================
    # CORE ENGINE
    # =========================================

    async def _process(
        self,
        db: AsyncSession,
        age_days: int,
        settlement_account_id: str,
        reserved_account_id: str
    ):

        cutoff = datetime.utcnow() - timedelta(days=age_days)

        result = await db.execute(
            select(EscrowAccount)
            .where(
                EscrowAccount.total_reserved > 0,
                EscrowAccount.created_at <= cutoff,
                EscrowAccount.status == "active"
            )
        )

        escrows = result.scalars().all()

        settled = []

        for escrow in escrows:

            amount = escrow.total_reserved

            if amount <= 0:
                continue

            reference = (
                f"SETTLEMENT-{escrow.id}-{datetime.utcnow().timestamp()}"
            )

            await self.financial.escrow_release(
                db=db,
                escrow_id=escrow.id,
                amount=amount,
                reference=reference,
                settlement_ledger_account=settlement_account_id,
                reserved_ledger_account=reserved_account_id
            )

            settled.append({
                "escrow_id": escrow.id,
                "amount": str(amount),
                "reference": reference
            })

        return {
            "processed": len(settled),
            "settlements": settled
        }