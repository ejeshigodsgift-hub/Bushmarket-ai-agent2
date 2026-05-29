from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db.models.agent_task import AgentTask
from app.db.models.outbox_event import OutboxEvent
from app.core.task_state_machine import TaskStateMachine


class AgentTaskLifecycle:

    async def update_status(
        self,
        db: AsyncSession,
        task_id: str,
        new_status: str
    ):
        # =========================
        # FETCH TASK
        # =========================
        result = await db.execute(
            select(AgentTask).where(
                AgentTask.id == task_id
            )
        )

        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(404, "Task not found")

        # =========================
        # STATE VALIDATION
        # =========================
        TaskStateMachine.validate_transition(
            task.status,
            new_status
        )

        # =========================
        # APPLY STATE CHANGE
        # =========================
        task.status = new_status

        if new_status in ["completed", "failed"]:
            task.completed_at = datetime.now(timezone.utc)

        # =========================
        # OUTBOX EVENT (CRITICAL)
        # =========================
        db.add(
            OutboxEvent(
                topic="agent.task.updated",
                payload={
                    "task_id": task.id,
                    "status": task.status
                }
            )
        )

        # =========================
        # COMMIT ONCE (UNIT OF WORK)
        # =========================
        await db.commit()

        await db.refresh(task)

        return task