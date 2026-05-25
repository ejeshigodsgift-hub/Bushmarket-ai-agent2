from sqlalchemy.orm import Session
from app.db.models.user import User


class AgentVerificationService:

    # =========================
    # CHECK IF AGENT IS VALID
    # =========================
    def is_valid_agent(self, db: Session, user_id: str) -> bool:

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return False

        # REQUIRED GATE (CRITICAL)
        roles = [r.role for r in user.roles]

        if "agent" not in roles:
            return False

        if not getattr(user, "is_verified_agent", False):
            return False

        if getattr(user, "status", None) != "approved":
            return False

        return True


agent_verification_service = AgentVerificationService()