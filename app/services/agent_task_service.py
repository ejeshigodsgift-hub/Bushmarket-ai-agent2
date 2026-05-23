from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models.agent_task import AgentTask
from app.services.permission_service import PermissionService
from app.services.audit_service import AuditService
from app.integrations.kafka_client import event_bus
from app.integrations.redis_client import redis_client


class AgentTaskService:

    VALID_TASKS = [
        "product_sourcing",
        "delivery_check",
        "supplier_contact"
    ]

    def create_task(
        self,
        db: Session,
        admin_user,
        agent_id: str,
        task_type: str,
        payload: dict,
        cooperative_id: str = None
    ):

        # 1. RBAC CHECK (Fix #4)
        PermissionService().validate_permission(
            admin_user["roles"],
            "assign_agent_task"
        )

        # 2. VALIDATION (Fix #3)
        if task_type not in self.VALID_TASKS:
            raise HTTPException(400, "Invalid task type")

        # 3. AGENT CHECK
        agent_exists = admin_user["db"].query(AgentTask).filter_by(id=agent_id).first()
        if not agent_exists:
            raise HTTPException(404, "Agent not found")

        # 4. TRANSACTION SAFE CREATION (Fix #2)
        task = AgentTask(
            agent_id=agent_id,
            admin_id=admin_user["id"],
            task_type=task_type,
            payload=payload,
            cooperative_id=cooperative_id,
            status="assigned"
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        # 5. REDIS LIVE STATE (Fix #5)
        redis_client.set(
            f"agent_task:{task.id}",
            str(task.status),
            ttl=86400
        )

        # 6. KAFKA EVENT (Fix #5)
        event_bus.publish("agent.task.created", {
            "task_id": task.id,
            "agent_id": agent_id,
            "task_type": task_type
        })

        # 7. AUDIT LOG (Fix #7)
        AuditService().log(
            db,
            user_id=admin_user["id"],
            action="CREATE_AGENT_TASK",
            entity_type="agent_task",
            entity_id=task.id,
            metadata=payload,
            ip=admin_user.get("ip")
        )

        return task