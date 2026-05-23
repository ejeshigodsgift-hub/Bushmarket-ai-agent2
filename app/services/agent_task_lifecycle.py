from sqlalchemy.orm import Session
from app.db.models.agent_task import AgentTask
from app.integrations.kafka_client import event_bus
from app.integrations.redis_client import redis_client


class AgentTaskLifecycle:

    def update_status(self, db: Session, task_id: str, new_status: str):

        task = db.query(AgentTask).filter_by(id=task_id).first()

        if not task:
            return None

        task.status = new_status

        if new_status in ["completed", "failed"]:
            task.completed_at = "now"

        db.commit()

        # Redis sync
        redis_client.set(f"agent_task:{task_id}", new_status, ttl=86400)

        # Kafka lifecycle event
        event_bus.publish("agent.task.updated", {
            "task_id": task_id,
            "status": new_status
        })

        return task