from sqlalchemy.orm import Session
from app.db.models.user import User
from app.db.models.role import Role
from app.core.security import hash_password, verify_password
from app.services.session_service import SessionService


class AuthService:

    def signup(self, db: Session, data: dict):
        user = User(
            full_name=data["full_name"],
            email=data["email"],
            phone=data.get("phone"),
            password_hash=hash_password(data["password"])
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        db.add(Role(user_id=user.id, role="shopper"))
        db.commit()

        return user

    def login(self, db: Session, email: str, password: str, request_meta: dict):
        user = db.query(User).filter(User.email == email).first()

        if not user or not verify_password(password, user.password_hash):
            return None

        session_service = SessionService()
        token, refresh = session_service.create_session(
            user.id,
            request_meta
        )

        return {
            "session_token": token,
            "refresh_token": refresh,
            "user": user
        }


auth_service = AuthService()