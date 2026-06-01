from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.role import Role

from app.core.security import (
    hash_password,
    verify_password
)

from app.services.session_service import SessionService
from app.services.outbox_service import outbox_service


class AuthService:

    # =========================================
    # SIGNUP (EMAIL OR PHONE REQUIRED)
    # =========================================
    async def signup(
        self,
        db: AsyncSession,
        data: dict
    ):

        email = data.get("email")
        phone = data.get("phone")

        # -----------------------------------------
        # VALIDATION: must have email OR phone
        # -----------------------------------------
        if not email and not phone:
            return None

        # -----------------------------------------
        # CHECK EXISTING USER (email OR phone)
        # -----------------------------------------
        existing = await db.execute(
            select(User).where(
                (User.email == email) if email else False,
            )
        )

        user_exists = existing.scalar_one_or_none()

        if user_exists:
            return None

        # optional: phone uniqueness check
        if phone:
            phone_check = await db.execute(
                select(User).where(User.phone == phone)
            )
            if phone_check.scalar_one_or_none():
                return None

        try:

            # -----------------------------------------
            # CREATE USER
            # -----------------------------------------
            user = User(
                full_name=data["full_name"],
                email=email,
                phone=phone,
                password_hash=hash_password(data["password"])
            )

            db.add(user)
            await db.flush()

            # -----------------------------------------
            # DEFAULT ROLE = SHOPPER
            # -----------------------------------------
            role = Role(
                user_id=user.id,
                role="shopper"
            )

            db.add(role)

            # -----------------------------------------
            # OUTBOX EVENT
            # -----------------------------------------
            await outbox_service.queue_event(
                db=db,
                topic="user.created",
                payload={
                    "user_id": user.id,
                    "email": user.email,
                    "phone": user.phone,
                    "role": "shopper"
                }
            )

            await db.commit()
            await db.refresh(user)

            return user

        except Exception:
            await db.rollback()
            raise

    # =========================================
    # LOGIN (EMAIL OR PHONE)
    # =========================================
    async def login(
        self,
        db: AsyncSession,
        identifier: str,
        password: str,
        request_meta: dict
    ):

        # -----------------------------------------
        # FIND USER BY EMAIL OR PHONE
        # -----------------------------------------
        result = await db.execute(
            select(User).where(
                (User.email == identifier) |
                (User.phone == identifier)
            )
        )

        user = result.scalar_one_or_none()

        if not user:
            return None

        # -----------------------------------------
        # VERIFY PASSWORD
        # -----------------------------------------
        if not verify_password(password, user.password_hash):
            return None

        try:

            # -----------------------------------------
            # CREATE SESSION
            # -----------------------------------------
            session = await SessionService().create_session(
                db=db,
                user_id=user.id,
                meta=request_meta
            )

            # -----------------------------------------
            # OUTBOX EVENT
            # -----------------------------------------
            await outbox_service.queue_event(
                db=db,
                topic="user.logged_in",
                payload={
                    "user_id": user.id,
                    "session_id": session.id
                }
            )

            await db.commit()

            return {
                "session_token": session.session_token,
                "refresh_token": session.refresh_token,
                "session": session,
                "user": user
            }

        except Exception:
            await db.rollback()
            raise


auth_service = AuthService()