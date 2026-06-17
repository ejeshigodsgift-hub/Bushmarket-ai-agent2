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
    AGENT APPLICATION ORCHESTRATOR

    RESPONSIBILITIES
    ----------------
    - Review applications
    - Approve applications
    - Reject applications
    - Suspend applications

    APPROVAL WORKFLOW
    -----------------
    1. Approve AgentApplication
    2. Approve MarketAgent
    3. Assign Agent Role

    This service is the ONLY place that coordinates
    the complete agent onboarding workflow.
    """

    def __init__(self):
        self.market_admin_service = MarketAdminService()
        self.agent_service = AgentService()
        self.audit = AuditService()

    # =========================================
    # APPROVE APPLICATION
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
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )

        if application.status == "approved":
            return application

        if application.status == "suspended":
            raise HTTPException(
                status_code=400,
                detail="Application is suspended"
            )

        # =====================================
        # APPLICATION APPROVAL
        # =====================================
        application.status = "approved"
        application.reviewed_by = admin_id
        application.reviewed_at = datetime.now(
            timezone.utc
        )

        # =====================================
        # STEP 1:
        # MARKET AGENT APPROVAL
        # =====================================
        await self.market_admin_service.approve_agent(
            db=db,
            user_id=str(application.user_id),
            admin_id=admin_id
        )

        # =====================================
        # STEP 2:
        # ROLE ASSIGNMENT
        # =====================================
        await self.agent_service.approve_agent(
            db=db,
            user_id=str(application.user_id),
            admin_id=admin_id
        )

        # =====================================
        # AUDIT
        # =====================================
        await self.audit.log(
            db=db,
            user_id=admin_id,
            action="agent_application_approved",
            entity_type="agent_application",
            entity_id=str(application.id),
            metadata={
                "application_id": str(application.id),
                "applicant_user_id": str(
                    application.user_id
                )
            }
        )

        # =====================================
        # OUTBOX EVENT
        # =====================================
        await outbox_service.queue_event(
            db=db,
            topic="agent.application.approved",
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
    # REJECT APPLICATION
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
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )

        application.status = "rejected"
        application.reviewed_by = admin_id
        application.reviewed_at = datetime.now(
            timezone.utc
        )
        application.rejection_reason = reason

        await self.audit.log(
            db=db,
            user_id=admin_id,
            action="agent_application_rejected",
            entity_type="agent_application",
            entity_id=str(application.id),
            metadata={
                "reason": reason
            }
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

    # =========================================
    # SUSPEND APPLICATION
    # =========================================
    async def suspend_application(
        self,
        db: AsyncSession,
        application_id: str,
        admin_id: str,
        reason: str | None = None
    ):

        result = await db.execute(
            select(AgentApplication).where(
                AgentApplication.id == application_id
            )
        )

        application = result.scalar_one_or_none()

        if not application:
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )

        application.status = "suspended"
        application.reviewed_by = admin_id
        application.reviewed_at = datetime.now(
            timezone.utc
        )

        await outbox_service.queue_event(
            db=db,
            topic="agent.application.suspended",
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