from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.role import Role

from app.core.security import (
    hash_password,
    verify_password
)

from app.services.session_service import SessionService


class AuthService:

    # =========================================
    # SIGNUP (FIXED DUPLICATE EMAIL BUG)
    # =========================================
    async def signup(self, db: AsyncSession, data: dict):

        existing = await db.execute(
            select(User).where(User.email == data["email"])
        )

        if existing.scalar_one_or_none():
            return None  # or raise HTTPException in controller

        user = User(
            full_name=data["full_name"],
            email=data["email"],
            phone=data.get("phone"),
            password_hash=hash_password(data["password"])
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        role = Role(
            user_id=user.id,
            role="shopper"
        )

        db.add(role)
        await db.commit()

        return user

    # =========================================
    # LOGIN (SESSION SAFE)
    # =========================================
    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        request_meta: dict
    ):

        result = await db.execute(
            select(User).where(User.email == email)
        )

        user = result.scalar_one_or_none()

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        session = await SessionService().create_session(
            db=db,
            user_id=user.id,
            meta=request_meta
        )

        return {
            "session_token": session.session_token,
            "refresh_token": session.refresh_token,
            "user": user
        }


auth_service = AuthService()