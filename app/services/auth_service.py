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
from app.services.shopper_profile_service import shopper_profile_service


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
        result = await db.execute(
            select(User).where(
                (User.email == email) if email else False
            )
        )

        if result.scalar_one_or_none():
            return None

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
            # DEFAULT SHOPPER PROFILE (AUTO CREATE)
            # -----------------------------------------
            await shopper_profile_service.create_default_profile(
                db=db,
                user_id=user.id,
                email=user.email,
                phone=user.phone
            )

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
    # app/services/auth_service.py

    async def login(
        self,
        db: AsyncSession,
        identifier: str,
        password: str,
        request_meta: dict
    ):

        result = await db.execute(
            select(User).where(
                (User.email == identifier) |
                (User.phone == identifier.   )
            )
        )

        user = result.scalar_one_or_none()

        if not user:
            return None

        if not verify_password(password,     user.password_hash):
            return None

        roles = user.role_list   # ✅ FIX 3

        session = await     SessionService().create_session(
            db=db,
            user_id=user.id,
            meta=request_meta | {
                "roles": roles   # ✅     embedded roles
            }
        )

        await outbox_service.queue_event(
            db=db,
           topic="user.logged_in",
            payload={
                "user_id": user.id,
                "session_id": session.id,
                "roles": roles
            }
        )

        await db.commit()
        await db.refresh(session)

        access_token =         jwt_service.create_access_token(
            user_id=user.id,
            roles=roles,
            session_id=session.id,
    cooperative_id=session.cooperative_id
    )
        

        return {
            "session_token":  session.session_token,
            "refresh_token":  session.refresh_token,
            "session": session,
            "user": user,
            "roles": roles
        }