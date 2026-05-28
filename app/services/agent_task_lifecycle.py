from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from app.db.models.agent_task import AgentTask

from app.integrations.kafka_client import event_bus
from app.integrations.redis_client import redis_client

from app.core.task_state_machine import TaskStateMachine


class AgentTaskLifecycle:

    async def update_status(
        self,
        db: AsyncSession,
        task_id: str,
        new_status: str
    ):

        result = await db.execute(
            select(AgentTask).where(
                AgentTask.id == task_id
            )
        )

        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(404, "Task not found")

        # =========================================
        # STATE VALIDATION
        # =========================================

        TaskStateMachine.validate_transition(
            task.status,
            new_status
        )

        task.status = new_status

        if new_status in [
            "completed",
            "failed"
        ]:
            task.completed_at = datetime.now(
                timezone.utc
            )

        await db.commit()

        await redis_client.set(
            f"agent_task:{task.id}",
            {
                "status": task.status
            },
            ttl=86400
        )

        await event_bus.publish(
            "agent.task.updated",
            {
                "task_id": task.id,
                "status": task.status
            }
        )

        return task