from sqlalchemy.orm import Session
from app.db.models.role import Role


class AgentService:

    def approve_agent(
        self,
        db: Session,
        user_id: str,
        admin_id: str
    ):

        role = Role(
            user_id=user_id,
            role="agent"
        )

        db.add(role)
        db.commit()

        return {
            "status": "approved",
            "user_id": user_id
        }