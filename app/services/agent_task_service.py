from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from app.db.models.agent_task import AgentTask
from app.db.models.role import Role

from app.services.permission_service import PermissionService
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
        cooperative_id: str = None
    ):
        # =========================================
        # PERMISSION CHECK
        # =========================================
        PermissionService().validate_permission(
            admin_user["roles"],
            "assign_agent_task"
        )

        if task_type not in self.VALID_TASKS:
            raise HTTPException(400, "Invalid task type")

        # =========================================
        # VERIFY AGENT ROLE
        # =========================================
        role_stmt = select(Role).where(
            Role.user_id == agent_id,
            Role.role == "agent"
        )

        role_result = await db.execute(role_stmt)
        agent_role = role_result.scalar_one_or_none()

        if not agent_role:
            raise HTTPException(404, "Agent not found")

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
        # BUSINESS WRITE (DB ONLY)
        # =========================================
        task = AgentTask(
            agent_id=agent_id,
            admin_id=admin_user["id"],
            task_type=task_type,
            payload=payload,
            cooperative_id=cooperative_id,
            status="assigned"
        )

        db.add(task)

        # =========================================
        # OUTBOX EVENT (SAME TRANSACTION)
        # =========================================
        outbox_repo = OutboxRepository()

        outbox_repo.add_event(
            db=db,
            topic="agent.task.created",
            payload={
                "task_id": task.id,
                "agent_id": agent_id,
                "task_type": task_type
            }
        )

        # =========================================
        # AUDIT LOG (OPTIONAL - still DB bound)
        # =========================================
        # If your audit service writes DB, keep it inside same transaction
        # Otherwise move it to outbox too in future scaling phase

        await db.commit()
        await db.refresh(task)

        return task