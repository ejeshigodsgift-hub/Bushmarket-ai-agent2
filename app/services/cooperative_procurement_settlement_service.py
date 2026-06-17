from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative
from app.db.models.financial_transaction import FinancialTransaction
from app.db.models.agent_task import AgentTask
from app.db.models.market_agent import MarketAgent

from app.services.financial_core_service import FinancialCoreService
from app.services.cooperative_state_service import cooperative_state_service
from app.services.outbox_service import outbox_service
from app.services.idempotency_service import idempotency_service


class CooperativeProcurementSettlementService:

    def __init__(self):
        self.financial = FinancialCoreService()

    async def process_procurement_settlement(
        self,
        db: AsyncSession,
        cooperative_id: str,
        escrow_id: str,
        agent_id: str,
        supplier_reference: str,
        invoice_reference: str,
        amount: Decimal,
        settlement_reference: str,
        reserved_ledger_account: str,
        available_ledger_account: str,
        settlement_ledger_account: str,
        fulfillment_context: dict,
        agent_verified: bool,
        admin_approved: bool
    ):

        # =====================================================
        # 1. IDEMPOTENCY
        # =====================================================
        await idempotency_service.ensure(db=db, key=settlement_reference)

        # =====================================================
        # 2. LOAD COOPERATIVE
        # =====================================================
        cooperative = await db.get(Cooperative, cooperative_id)
        if not cooperative:
            raise HTTPException(404, "Cooperative not found")

        # =====================================================
        # 3. VALIDATE AGENT ENTITY (NEW)
        # =====================================================
        agent = await db.get(MarketAgent, agent_id)
        if not agent:
            raise HTTPException(404, "Agent not found")

        if not agent.is_active:
            raise HTTPException(403, "Agent is not active")

        # =====================================================
        # 4. VERIFY AGENT TASK (CRITICAL NEW CONTROL LAYER)
        # =====================================================
        task_query = await db.execute(
            select(AgentTask)
            .where(AgentTask.agent_id == agent_id)
            .where(AgentTask.cooperative_id == cooperative_id)
            .where(AgentTask.status == "completed")
        )

        agent_task = task_query.scalar_one_or_none()

        if not agent_task:
            raise HTTPException(403, "No completed agent task found")

        # =====================================================
        # 5. AGENT VERIFICATION GATE
        # =====================================================
        if not agent_verified:
            raise HTTPException(403, "Agent verification required")

        # =====================================================
        # 6. ADMIN APPROVAL GATE
        # =====================================================
        if not admin_approved:
            raise HTTPException(403, "Admin approval required")

        # =====================================================
        # 7. FULFILLMENT CONTEXT (NOW TASK-BASED TRUTH)
        # =====================================================
        required_context = {
            "supplier": "external_reference_only",
            "agent_id": agent_id,
            "admin_approval_status": "approved",
            "verification_level": "agent_confirmed",
            "task_id": agent_task.id
        }

        for k, v in required_context.items():
            if fulfillment_context.get(k) != v:
                raise HTTPException(400, f"Invalid fulfillment context: {k}")

        # =====================================================
        # 8. ESCROW HOLD
        # =====================================================
        await self.financial.escrow_hold(
            db=db,
            escrow_id=escrow_id,
            amount=amount,
            reference=f"HOLD-{settlement_reference}",
            reserved_ledger_account=reserved_ledger_account,
            available_ledger_account=available_ledger_account
        )

        # =====================================================
        # 9. SUPPLIER VALIDATION (EXTERNAL ONLY)
        # =====================================================
        if not supplier_reference:
            raise HTTPException(400, "Supplier reference required")

        # =====================================================
        # 10. ESCROW RELEASE (BUSHMARKET = VENDOR OF RECORD)
        # =====================================================
        await self.financial.escrow_release(
            db=db,
            escrow_id=escrow_id,
            amount=amount,
            reference=f"RELEASE-{settlement_reference}",
            settlement_ledger_account=settlement_ledger_account,
            reserved_ledger_account=reserved_ledger_account
        )

        # =====================================================
        # 11. SETTLEMENT RECORD (NOW REAL ENTITY LINKAGE)
        # =====================================================
        tx = FinancialTransaction(
            reference=settlement_reference,
            transaction_type="procurement_settlement",
            amount=amount,
            escrow_account_id=escrow_id,
            status="completed",
            created_by="system",
            metadata={
                "cooperative_id": cooperative_id,
                "agent_id": agent_id,
                "agent_task_id": agent_task.id,
                "supplier_reference": supplier_reference,
                "invoice_reference": invoice_reference,
                "vendor_of_record": "bushmarket"
            }
        )

        db.add(tx)

        # =====================================================
        # 12. STATE TRANSITION
        # =====================================================
        await cooperative_state_service.transition(
            db=db,
            cooperative=cooperative,
            new_state="purchasing",
            reason="verified agent-task driven procurement settlement"
        )

        # =====================================================
        # 13. OUTBOX EVENT
        # =====================================================
        await outbox_service.queue_event(
            db=db,
            topic="cooperative.procurement.settled",
            payload={
                "cooperative_id": cooperative_id,
                "agent_id": agent_id,
                "agent_task_id": agent_task.id,
                "amount": str(amount),
                "reference": settlement_reference,
                "vendor_of_record": "bushmarket"
            }
        )

        return {
            "status": "success",
            "cooperative_id": cooperative_id,
            "agent_id": agent_id,
            "agent_task_id": agent_task.id,
            "supplier_reference": supplier_reference,
            "vendor": "bushmarket",
            "settlement_reference": settlement_reference
        }