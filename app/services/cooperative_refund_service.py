from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership
from app.db.models.cooperative_contribution import CooperativeContribution
from app.db.models.cooperative_refund import CooperativeRefund

from app.services.financial_core_service import FinancialCoreService
from app.services.outbox_service import outbox_service


class CooperativeRefundService:
    """
    Handles ALL cooperative refund scenarios:

    - Cooperative expiration refunds
    - Failed procurement refunds
    - Merge rollback refunds
    - Admin override refunds
    - Dispute refunds

    NOTE:
    FinancialCoreService performs actual money movement.
    This service ONLY orchestrates + records + triggers workflows.
    """

    def __init__(self):
        self.financial_core = FinancialCoreService()

    # =========================================================
    # MAIN ENTRY: DISPATCH REFUND FLOW
    # =========================================================
    async def process_cooperative_refund(
        self,
        db: AsyncSession,
        cooperative_id: str,
        refund_reason: str,
        refund_type: str = "full",
        admin_notes: Optional[str] = None
    ) -> List[CooperativeRefund]:

        coop = await db.get(Cooperative, cooperative_id)

        if not coop:
            raise ValueError("Cooperative not found")

        # fetch all active contributions
        stmt = select(CooperativeContribution).where(
            CooperativeContribution.cooperative_id == cooperative_id,
            CooperativeContribution.status == "completed"
        )

        result = await db.execute(stmt)
        contributions = result.scalars().all()

        if not contributions:
            return []

        refunds: List[CooperativeRefund] = []

        for contribution in contributions:
            refund = await self._create_member_refund(
                db=db,
                cooperative=coop,
                contribution=contribution,
                refund_reason=refund_reason,
                refund_type=refund_type,
                admin_notes=admin_notes
            )
            refunds.append(refund)

        await db.commit()

        await outbox_service.queue_event(
            db,
            "cooperative.refund.processed",
            {
                "cooperative_id": cooperative_id,
                "refund_reason": refund_reason,
                "total_refunds": len(refunds)
            }
        )

        return refunds

    # =========================================================
    # CORE REFUND CREATION (PER MEMBER)
    # =========================================================
    async def _create_member_refund(
        self,
        db: AsyncSession,
        cooperative: Cooperative,
        contribution: CooperativeContribution,
        refund_reason: str,
        refund_type: str,
        admin_notes: Optional[str]
    ) -> CooperativeRefund:

        # prevent duplicate refund
        existing_stmt = select(CooperativeRefund).where(
            CooperativeRefund.contribution_id == contribution.id
        )

        existing = (await db.execute(existing_stmt)).scalar_one_or_none()

        if existing:
            return existing

        refund_amount = Decimal(str(contribution.amount))

        refund = CooperativeRefund(
            cooperative_id=cooperative.id,
            membership_id=contribution.membership_id,
            user_id=contribution.user_id,
            contribution_id=contribution.id,
            refund_amount=refund_amount,
            refund_reason=refund_reason,
            refund_type=refund_type,
            status="pending",
            admin_notes=admin_notes,
            refund_reference=f"refund_{datetime.utcnow().timestamp()}",
            funding_round=getattr(contribution, "funding_round", 1),
            is_partial_procurement_related=False,
            created_at=datetime.now(timezone.utc)
        )

        db.add(refund)
        await db.flush()

        # trigger financial execution asynchronously via outbox
        await outbox_service.queue_event(
            db,
            "cooperative.refund.requested",
            {
                "refund_id": refund.id,
                "cooperative_id": cooperative.id,
                "user_id": contribution.user_id,
                "amount": str(refund_amount),
                "reason": refund_reason
            }
        )

        return refund

    # =========================================================
    # EXECUTE REFUND (FINANCIAL CORE INTEGRATION)
    # =========================================================
    async def execute_refund(
        self,
        db: AsyncSession,
        refund_id: str,
        escrow_id: str,
        debit_ledger_account: str,
        credit_ledger_account: str,
        settlement_ledger_account: str,
        reserved_ledger_account: str
    ) -> CooperativeRefund:

        refund = await db.get(CooperativeRefund, refund_id)

        if not refund:
            raise ValueError("Refund not found")

        if refund.status in ["completed", "processing"]:
            return refund

        refund.status = "processing"

        await db.flush()

        # Move funds via FinancialCore (escrow release → wallet/ledger settlement)
        await self.financial_core.escrow_release(
            db=db,
            escrow_id=escrow_id,
            amount=Decimal(str(refund.refund_amount)),
            reference=refund.refund_reference,
            settlement_ledger_account=settlement_ledger_account,
            reserved_ledger_account=reserved_ledger_account
        )

        refund.status = "completed"
        refund.processed_at = datetime.now(timezone.utc)

        await db.flush()

        await outbox_service.queue_event(
            db,
            "cooperative.refund.completed",
            {
                "refund_id": refund.id,
                "user_id": refund.user_id,
                "amount": str(refund.refund_amount),
                "cooperative_id": refund.cooperative_id
            }
        )

        return refund

    # =========================================================
    # EXPIRATION REFUND AUTOMATION
    # =========================================================
    async def process_expired_cooperative_refund(
        self,
        db: AsyncSession,
        cooperative_id: str
    ):
        return await self.process_cooperative_refund(
            db=db,
            cooperative_id=cooperative_id,
            refund_reason="cooperative_expired",
            refund_type="full"
        )

    # =========================================================
    # FAILED PROCUREMENT REFUND
    # =========================================================
    async def process_failed_procurement_refund(
        self,
        db: AsyncSession,
        cooperative_id: str
    ):
        return await self.process_cooperative_refund(
            db=db,
            cooperative_id=cooperative_id,
            refund_reason="procurement_failed",
            refund_type="partial"
        )

    # =========================================================
    # ADMIN OVERRIDE REFUND
    # =========================================================
    async def admin_override_refund(
        self,
        db: AsyncSession,
        cooperative_id: str,
        admin_notes: str
    ):
        return await self.process_cooperative_refund(
            db=db,
            cooperative_id=cooperative_id,
            refund_reason="admin_override",
            refund_type="full",
            admin_notes=admin_notes
        )

    # =========================================================
    # DISPUTE RESOLUTION REFUND
    # =========================================================
    async def process_dispute_refund(
        self,
        db: AsyncSession,
        cooperative_id: str
    ):
        return await self.process_cooperative_refund(
            db=db,
            cooperative_id=cooperative_id,
            refund_reason="dispute_resolution",
            refund_type="partial"
        )