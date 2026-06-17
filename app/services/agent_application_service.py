# =========================================
# FILE: app/services/agent_application_service.py
# =========================================

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agent_application import AgentApplication

from app.services.market_admin_service import MarketAdminService
from app.services.agent_service import AgentService
from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service


class AgentApplicationService:
    """
    ORCHESTRATOR ONLY (NO BUSINESS WRITE LOGIC)

    It only:
    - validates application
    - triggers approval requests
    - delegates actual approval to domain services
    """

    def __init__(self):
        self.market_admin_service = MarketAdminService()
        self.agent_service = AgentService()
        self.audit = AuditService()

    # =========================================
    # APPROVE APPLICATION (ORCHESTRATION ONLY)
    # =========================================
    async def approve_application(
        self,
        db: AsyncSession,
        application_id: str,
        admin_id: str
    ):

        result = await db.execute(
            select(AgentApplication).where(
                AgentApplication.id == application_id
            )
        )

        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(404, "Application not found")

        if application.status in ["approved", "approval_requested"]:
            return application

        

        if application.status == "suspended":
            raise HTTPException(400, "Application is suspended")

        # =========================================
        # MARK APPLICATION AS PENDING APPROVAL FLOW
        # =========================================
        application.status = "approval_requested"
        application.reviewed_by = admin_id
        application.reviewed_at = datetime.now(timezone.utc)

        # =========================================
        # STEP 1 (REQUEST MARKET APPROVAL)
        # =========================================
        await outbox_service.queue_event(
            db=db,
            topic="agent.market_approval.requested",
            payload={
                "user_id": str(application.user_id),
                "admin_id": admin_id,
                "application_id": str(application.id)
            }
        )

      
        # =========================================
        # STEP 2 (REQUEST ROLE APPROVAL)
        # =========================================
        await outbox_service.queue_event(
            db=db,
            topic="agent.role_approval.requested",
            payload={
                "user_id": str(application.user_id),
                "admin_id": admin_id,
                "application_id": str(application.id)
            }
        )

        

        # =========================================
        # AUDIT ONLY (NO APPROVAL LOGIC HERE)
        # =========================================
        await self.audit.log(
            db=db,
            user_id=admin_id,
            action="agent_application_processed",
            entity_type="agent_application",
            entity_id=str(application.id),
            metadata={
                "application_id": str(application.id),
                "user_id": str(application.user_id)
            }
        )

        # =========================================
        # FINAL OUTBOX EVENT
        # =========================================
        await outbox_service.queue_event(
            db=db,
            topic="agent.application.processed",
            payload={
                "application_id": str(application.id),
                "user_id": str(application.user_id),
                "admin_id": admin_id
            }
        )

        await db.commit()
        await db.refresh(application)

        return application

    # =========================================
    # REJECT APPLICATION (UNCHANGED LOGIC STYLE)
    # =========================================
    async def reject_application(
        self,
        db: AsyncSession,
        application_id: str,
        admin_id: str,
        reason: str
    ):

        result = await db.execute(
            select(AgentApplication).where(
                AgentApplication.id == application_id
            )
        )

        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(404, "Application not found")

        application.status = "rejected"
        application.reviewed_by = admin_id
        application.reviewed_at = datetime.now(timezone.utc)
        application.rejection_reason = reason

        await self.audit.log(
            db=db,
            user_id=admin_id,
            action="agent_application_rejected",
            entity_type="agent_application",
            entity_id=str(application.id),
            metadata={"reason": reason}
        )

        await outbox_service.queue_event(
            db=db,
            topic="agent.application.rejected",
            payload={
                "application_id": str(application.id),
                "user_id": str(application.user_id),
                "admin_id": admin_id,
                "reason": reason
            }
        )

        await db.commit()
        await db.refresh(application)

        return application


agent_application_service = AgentApplicationService()