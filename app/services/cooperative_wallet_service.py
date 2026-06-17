from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.db.models.milestone_event import MilestoneEvent

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership
from app.db.models.cooperative_contribution import CooperativeContribution
from app.db.models.cooperative_refund import CooperativeRefund
from app.db.models.escrow_account import EscrowAccount
from app.db.models.financial_reconciliation import FinancialReconciliation

from app.services.financial_core_service import FinancialCoreService
from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from sqlalchemy import select

class CooperativeWalletService:
    """
    COOPERATIVE WALLET SERVICE (BUSINESS ORCHESTRATION LAYER)

    Responsibilities:
    - Wallet snapshot computation
    - Contribution tracking aggregation
    - Refund orchestration
    - Procurement wallet state mapping
    - Escrow + ledger reconciliation coordination
    - Dashboard data layer
    - AI notification triggers
    """

    def __init__(self):
        self.financial = FinancialCoreService()
        self.audit = AuditService()

    # =========================================================
    # 1. WALLET SNAPSHOT (CORE DASHBOARD ENGINE)
    # =========================================================
    async def get_wallet_snapshot(
        self,
        db: AsyncSession,
        cooperative: Cooperative
    ):
        result = await db.execute(
            select(EscrowAccount).where(
                EscrowAccount.cooperative_id ==  cooperative.id
            )
        )
        escrow = result.scalar_one_or_none()

        escrow_balance = escrow.available_balance if escrow else Decimal("0")
        reserved = escrow.total_reserved if escrow else Decimal("0")
        ledger = escrow.ledger_balance if escrow else Decimal("0")

        contributions = cooperative.total_contributed or 0

        return {
            "pool_balance": float(escrow_balance + reserved),
            "available_balance": float(escrow_balance),
            "reserved_balance": float(reserved),
            "escrow_balance": float(escrow_balance + reserved),
            "ledger_balance": float(ledger),
            "total_contributions": float(contributions)
        }

    # =========================================================
    # 2. PROGRESS LAYER
    # =========================================================
    async def get_progress_metrics(
        self,
        cooperative: Cooperative
    ):
        target = float(cooperative.target_amount or 0)
        current = float(cooperative.total_contributed or 0)

        funding_pct = (current / target * 100) if target > 0 else 0

        remaining_amount = max(target - current, 0)

        remaining_members = max(
            cooperative.max_members - cooperative.current_members,
            0
        )

        return {
            "funding_percentage": funding_pct,
            "remaining_amount": remaining_amount,
            "remaining_members": remaining_members,
            "estimated_completion": "auto-calculated-engine"
        }

    # =========================================================
    # 3. EXTENSION LAYER
    # =========================================================
    async def get_extension_state(self, cooperative: Cooperative):

        return {
            "can_extend": cooperative.status in ["expired", "active"],
            "extension_window_open": cooperative.status == "expired",
            "extension_deadline": getattr(cooperative, "expiry_extended_at", None),
            "vote_counts": {
                "extend": 0,
                "procurement": 0
            }
        }

    # =========================================================
    # 4. PROCUREMENT LAYER
    # =========================================================
    async def get_procurement_state(self, cooperative: Cooperative):

        funded = float(cooperative.total_contributed or 0) >= float(cooperative.target_amount or 0)

        return {
            "funded_status": funded,
            "purchasing_status": cooperative.status == "purchasing",
            "delivery_status": cooperative.status == "delivered",
            "closed_status": cooperative.status == "closed"
        }

    # =========================================================
    # 5. FINANCIAL BREAKDOWN LAYER
    # =========================================================
    async def get_financial_breakdown(self, cooperative: Cooperative):

        escrow = cooperative.escrow_balance or 0
        spent = 0  # derived from procurement engine
        refunded = 0  # derived from refund table

        available = float(escrow) - float(spent)

        return {
            "total_contributions": float(cooperative.total_contributed or 0),
            "total_reserved": float(escrow),
            "total_spent": float(spent),
            "total_refunded": float(refunded),
            "available_purchasing_power": available
        }

    # =========================================================
    # 6. RECONCILIATION LAYER
    # =========================================================
    async def get_reconciliation_state(
        self,
        db: AsyncSession,
        cooperative: Cooperative
    ):

        reconciliation = await db.execute(
            FinancialReconciliation.__table__.select().where(
                FinancialReconciliation.cooperative_id == cooperative.id
            )
        )

        records = reconciliation.fetchall()

        status = "healthy"

        if records:
            for r in records:
                if r.status == "mismatch":
                    status = "attention_required"

        return {
            "cooperative_balance": float(cooperative.total_contributed or 0),
            "escrow_balance": float(cooperative.escrow_balance or 0),
            "ledger_balance": "computed_by_financial_core",
            "reconciliation_status": status
        }

    # =========================================================
    # 7. MEMBER ANALYTICS LAYER
    # =========================================================
    async def get_member_analytics(self, db: AsyncSession, cooperative: Cooperative):

        members = await db.execute(
            CooperativeMembership.__table__.select().where(
                CooperativeMembership.cooperative_id == cooperative.id
            )
        )

        members = members.fetchall()

        return {
            "active_members": len([m for m in members if m.status == "active"]),
            "pending_members": len([m for m in members if m.status == "pending"]),
            "failed_members": len([m for m in members if m.status == "failed"]),
            "refunded_members": len([m for m in members if m.status == "refunded"])
        }

    # =========================================================
    # 8. SAVINGS ANALYTICS LAYER
    # =========================================================
    async def get_savings_metrics(self, cooperative: Cooperative):

        retail_value = cooperative.target_amount * 1.25  # estimated markup model
        buying_value = cooperative.target_amount

        savings = retail_value - buying_value
        percent = (savings / retail_value * 100) if retail_value else 0

        return {
            "estimated_retail_value": float(retail_value),
            "cooperative_buying_value": float(buying_value),
            "estimated_savings": float(savings),
            "savings_percentage": float(percent)
        }

    # =========================================================
    # 9. AI NOTIFICATION TRIGGERS
    # =========================================================
    

    async def _trigger_milestone(self,  db, cooperative, milestone: str, message:  str):
        existing = await db.execute(
            select(MilestoneEvent).where(
                MilestoneEvent.cooperative_id == cooperative.id,
                MilestoneEvent.milestone == milestone
            )
        )

        if existing.scalar_one_or_none():
            return  # already triggered

        event = MilestoneEvent(
            cooperative_id=cooperative.id,
            milestone=milestone
        )

        db.add(event)

        await self._notify(cooperative,  message)
            
    async def _notify(self, cooperative: Cooperative, message: str):

        await outbox_service.queue_event(
            db=None,
            topic="cooperative.notification",
            payload={
                "cooperative_id": cooperative.id,
                "message": message
            }
        )

    # =========================================================
    # 10. REFUND ORCHESTRATION (NOT EXECUTION)
    # =========================================================
    async def initiate_refund(
        self,
        db: AsyncSession,
        cooperative: Cooperative,
        membership: CooperativeMembership,
        reason: str
    ):

        refund = CooperativeRefund(
            cooperative_id=cooperative.id,
            membership_id=membership.id,
            user_id=membership.user_id,
            refund_amount=membership.contribution_amount,
            refund_reason=reason,
            status="pending"
        )

        db.add(refund)

        await self.audit.log(
            db=db,
            user_id=membership.user_id,
            action="refund_initiated",
            entity_type="cooperative",
            entity_id=cooperative.id,
            metadata={"reason": reason}
        )

        return refund


# SINGLETON
cooperative_wallet_service = CooperativeWalletService()