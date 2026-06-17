from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from app.db.models.agent_task import AgentTask

from app.services.permission_service import PermissionService
from app.services.agent_permission_service import (
    agent_permission_service
)
from app.repositories.outbox_repository import OutboxRepository
from app.core.logger import logger


class AgentTaskService:

    VALID_TASKS = [
        "product_sourcing",
        "delivery_check",
        "supplier_contact"
    ]

    async def create_task(
        self,
        db: AsyncSession,
        admin_user: dict,
        agent_id: str,
        task_type: str,
        payload: dict,
        cooperative_id: str | None = None
    ):
        # =========================================
        # ADMIN PERMISSION CHECK
        # =========================================
        PermissionService().validate_permission(
            admin_user["roles"],
            "assign_agent_task"
        )

        # =========================================
        # TASK VALIDATION
        # =========================================
        if task_type not in self.VALID_TASKS:
            raise HTTPException(
                status_code=400,
                detail="Invalid task type"
            )

        # =========================================
        # VERIFY FULL AGENT STATUS
        #
        # Requires:
        # - Role(role="agent")
        # - MarketAgent.status="approved"
        # - MarketAgent.is_verified_agent=True
        # =========================================
        await agent_permission_service.require_agent(
            db=db,
            user_id=agent_id
        )

        # =========================================
        # LOGGING
        # =========================================
        logger.info(
            "Creating agent task",
            extra={
                "agent_id": agent_id,
                "task_type": task_type,
                "admin_id": admin_user["id"]
            }
        )

        # =========================================
        # CREATE TASK
        # =========================================
        task = AgentTask(
            agent_id=agent_id,
            admin_id=admin_user["id"],
            cooperative_id=cooperative_id,
            task_type=task_type,
            payload=payload,
            status="assigned"
        )

        db.add(task)

        await db.flush()

        # =========================================
        # OUTBOX EVENT
        # =========================================
        outbox_repo = OutboxRepository()

        outbox_repo.add_event(
            db=db,
            topic="agent.task.created",
            payload={
                "task_id": task.id,
                "agent_id": agent_id,
                "task_type": task_type,
                "cooperative_id": cooperative_id
            }
        )

        # =========================================
        # COMMIT
        # =========================================
        await db.commit()
        await db.refresh(task)

        return task