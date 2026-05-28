from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from app.db.models.agent_task import AgentTask
from app.db.models.role import Role

from app.integrations.kafka_client import event_bus
from app.integrations.redis_client import redis_client

from app.services.audit_service import AuditService
from app.services.permission_service import PermissionService


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

        PermissionService().validate_permission(
            admin_user["roles"],
            "assign_agent_task"
        )

        if task_type not in self.VALID_TASKS:
            raise HTTPException(400, "Invalid task type")

        role_stmt = select(Role).where(
            Role.user_id == agent_id,
            Role.role == "agent"
        )

        role_result = await db.execute(role_stmt)

        agent_role = role_result.scalar_one_or_none()

        if not agent_role:
            raise HTTPException(404, "Agent not found")

        task = AgentTask(
            agent_id=agent_id,
            admin_id=admin_user["id"],
            task_type=task_type,
            payload=payload,
            cooperative_id=cooperative_id,
            status="assigned"
        )

        db.add(task)

        await db.commit()
        await db.refresh(task)

        await redis_client.set(
            f"agent_task:{task.id}",
            {"status": task.status},
            ttl=86400
        )

        await event_bus.publish(
            "agent.task.created",
            {
                "task_id": task.id,
                "agent_id": task.agent_id,
                "task_type": task.task_type
            }
        )

        await AuditService().log(
            db=db,
            user_id=admin_user["id"],
            action="CREATE_AGENT_TASK",
            entity_type="agent_task",
            entity_id=task.id,
            metadata=payload
        )

        return task