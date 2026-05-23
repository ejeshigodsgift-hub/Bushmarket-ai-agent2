from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.role import Role

from app.core.security import (
    hash_password,
    verify_password
)

from app.services.session_service import SessionService
from app.services.audit_service import AuditService


class AuthService:

    # =========================
    # SIGNUP
    # =========================

    def signup(
        self,
        db: Session,
        data: dict
    ):

        user = User(
            full_name=data["full_name"],
            email=data["email"],
            phone=data.get("phone"),
            password_hash=hash_password(
                data["password"]
            )
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        role = Role(
            user_id=user.id,
            role="shopper"
        )

        db.add(role)
        db.commit()

        AuditService().log(
            db=db,
            user_id=user.id,
            action="USER_SIGNUP",
            entity_type="user",
            entity_id=user.id,
            metadata={
                "email": user.email
            }
        )

        return user

    # =========================
    # LOGIN
    # =========================

    def login(
        self,
        db: Session,
        email: str,
        password: str,
        request_meta: dict
    ):

        user = db.query(User).filter(
            User.email == email
        ).first()

        if not user:
            return None

        if not verify_password(
            password,
            user.password_hash
        ):
            return None

        session_service = SessionService()

        db_session = session_service.create_session(
            db=db,
            user_id=user.id,
            meta=request_meta
        )

        AuditService().log(
            db=db,
            user_id=user.id,
            action="LOGIN_SUCCESS",
            entity_type="session",
            entity_id=db_session.id,
            metadata={
                "ip_address": request_meta.get("ip_address"),
                "device_name": request_meta.get("device_name")
            }
        )

        return {
            "session_token": db_session.session_token,
            "refresh_token": db_session.refresh_token,
            "user": user
        }


auth_service = AuthService()