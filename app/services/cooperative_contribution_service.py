from decimal import Decimal
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership
from app.db.models.cooperative_contribution import CooperativeContribution
from app.db.models.escrow_account import EscrowAccount

from app.services.financial_core_service import FinancialCoreService
from app.services.outbox_service import outbox_service


class CooperativeContributionService:

    def __init__(self):
        self.financial = FinancialCoreService()

    # =====================================================
    # RECORD CONTRIBUTION (STRICT MEMBERSHIP CHECK)
    # =====================================================
    async def record_contribution(
        self,
        db: AsyncSession,
        cooperative_id: str,
        membership_id: str,
        user_id: str,
        payment_intent_id: str,
        payment_reference: str,
        escrow_account_id: str,
        amount: Decimal,
    ):

        cooperative = await db.get(Cooperative, cooperative_id)
        if not cooperative:
            raise HTTPException(404, "Cooperative not found")

        membership = await db.get(CooperativeMembership, membership_id)
        if not membership:
            raise HTTPException(404, "Membership not found")

        # -----------------------------
        # ENFORCE PAID MEMBERSHIP ONLY
        # -----------------------------
        if membership.payment_status != "paid":
            raise HTTPException(403, "Membership not fully paid")

        contribution = CooperativeContribution(
            cooperative_id=cooperative_id,
            membership_id=membership_id,
            user_id=user_id,
            amount=amount,
            payment_reference=payment_reference,
            payment_intent_id=payment_intent_id,
            status="completed",
            created_at=datetime.now(timezone.utc)
        )

        db.add(contribution)

        cooperative.total_contributed += amount

        if membership.status != "active":
            membership.status = "active"
            membership.activated_at = datetime.now(timezone.utc)
            cooperative.current_members += 1

        # -----------------------------
        # ESCROW SYNC
        # -----------------------------
        await self.financial.escrow_deposit(
            db=db,
            escrow_id=escrow_account_id,
            amount=amount,
            reference=f"coop_contribution_{contribution.id}",
            debit_ledger_account="escrow_debit",
            credit_ledger_account="escrow_credit"
        )

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.contribution.recorded",
            payload={
                "cooperative_id": cooperative_id,
                "membership_id": membership_id,
                "amount": str(amount)
            }
        )

        await db.commit()
        return contribution

    # =====================================================
    # REVERSE CONTRIBUTION
    # =====================================================
    async def reverse_contribution(self, db, contribution_id: str, reason: str):
        contribution = await db.get(CooperativeContribution, contribution_id)

        if not contribution:
            raise HTTPException(404, "Contribution not found")

        if contribution.status != "completed":
            raise HTTPException(400, "Already processed")

        cooperative = await db.get(Cooperative, contribution.cooperative_id)

        contribution.status = "reversed"
        contribution.notes = reason

        cooperative.total_contributed -= contribution.amount

        await db.commit()
        return contribution

    # =====================================================
    # REFUND CONTRIBUTION
    # =====================================================
    async def refund_contribution(self, db, contribution_id: str, reason: str):
        contribution = await db.get(CooperativeContribution, contribution_id)

        if not contribution:
            raise HTTPException(404, "Contribution not found")

        contribution.status = "refunded"
        contribution.notes = reason

        cooperative = await db.get(Cooperative, contribution.cooperative_id)
        cooperative.total_contributed -= contribution.amount

        membership = await db.get(CooperativeMembership, contribution.membership_id)
        if membership:
            membership.status = "refunded"
            membership.payment_status = "refunded"
            membership.refunded_at = datetime.now(timezone.utc)

        await db.commit()
        return contribution

    # =====================================================
    # TOTAL CALCULATION
    # =====================================================
    async def calculate_total(
        self,
        db: AsyncSession,
        cooperative_id: str
    ) -> Decimal:

        stmt = select(
            func.coalesce(
                func.sum(CooperativeContribution.amount),
                0
            )
        ).where(
            CooperativeContribution.cooperative_id == cooperative_id,
            CooperativeContribution.status == "completed"
        )

        result = await db.execute(stmt)

        return Decimal(str(result.scalar() or 0))

    # =====================================================
    # MEMBER COUNT SYNCHRONIZATION
    # =====================================================
    async def sync_member_count(
        self,
        db: AsyncSession,
        cooperative_id: str
    ) -> int:

        stmt = select(
            func.count(CooperativeMembership.id)
        ).where(
            CooperativeMembership.cooperative_id == cooperative_id,
            CooperativeMembership.status == "active"
        )

        result = await db.execute(stmt)

        count = result.scalar() or 0

        cooperative = await db.get(
            Cooperative,
            cooperative_id
        )

        if not cooperative:
            raise HTTPException(
                404,
                "Cooperative not found"
            )

        cooperative.current_members = count

        await db.commit()

        return count


cooperative_contribution_service = (
    CooperativeContributionService()
)