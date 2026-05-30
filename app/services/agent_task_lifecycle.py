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
    ) -> AgentTask:

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
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        # =========================
        # VALIDATE STATE TRANSITION
        # =========================
        TaskStateMachine.validate_transition(
            task.status,
            new_status
        )

        old_status = task.status

        # =========================
        # APPLY STATUS CHANGE
        # =========================
        task.status = new_status

        if new_status in ("completed", "failed"):
            task.completed_at = datetime.now(
                timezone.utc
            )

        # =========================
        # CREATE OUTBOX EVENT
        # =========================
        outbox_event = OutboxEvent(
            topic="agent.task.updated",
            payload={
                "task_id": task.id,
                "agent_id": task.agent_id,
                "old_status": old_status,
                "new_status": new_status,
                "updated_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }
        )

        db.add(outbox_event)

        # =========================
        # SINGLE TRANSACTION
        # =========================
        await db.commit()

        await db.refresh(task)

        return task