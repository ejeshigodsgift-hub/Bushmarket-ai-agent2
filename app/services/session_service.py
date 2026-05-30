from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.session import Session

from app.integrations.redis_client import redis_client

from app.core.security import (
    generate_session_token,
    generate_refresh_token,
    generate_device_fingerprint
)

from app.core.config import settings

from app.services.outbox_service import outbox_service


class SessionService:

    SESSION_PREFIX = "session:"

    # =========================================
    # CREATE SESSION
    # =========================================

    async def create_session(
        self,
        db: AsyncSession,
        user_id: str,
        meta: dict
    ):

        now = datetime.now(timezone.utc)

        fingerprint = generate_device_fingerprint(
            meta.get("ip_address", ""),
            meta.get("user_agent", "")
        )

        session_token = generate_session_token()
        refresh_token = generate_refresh_token()

        expires_at = now + timedelta(
            seconds=settings.SESSION_EXPIRE_SECONDS
        )

        refresh_expires_at = now + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        db_session = Session(
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token,
            device_id=meta.get("device_id"),
            device_name=meta.get("device_name"),
            user_agent=meta.get("user_agent"),
            ip_address=meta.get("ip_address"),
            fingerprint=fingerprint,
            expires_at=expires_at,
            refresh_expires_at=refresh_expires_at,
            is_active=True,
            is_revoked=False,
            last_seen_at=now
        )

        db.add(db_session)

        await db.flush()

        await outbox_service.queue_event(
            db=db,
            topic="session.created",
            payload={
                "session_id": db_session.id,
                "user_id": user_id,
                "device_id": db_session.device_id
            }
        )

        await db.commit()

        await db.refresh(db_session)

        await redis_client.set(
            self.SESSION_PREFIX + session_token,
            {
                "session_id": db_session.id,
                "user_id": user_id,
                "fingerprint": fingerprint
            },
            ttl=settings.SESSION_EXPIRE_SECONDS
        )

        return db_session

    # =========================================
    # DESTROY SESSION
    # =========================================

    async def destroy_session(
        self,
        db: AsyncSession,
        token: str
    ):

        result = await db.execute(
            select(Session).where(
                Session.session_token == token
            )
        )

        db_session = result.scalar_one_or_none()

        if not db_session:
            return

        db_session.is_active = False
        db_session.is_revoked = True
        db_session.revoked_at = datetime.now(timezone.utc)

        await outbox_service.queue_event(
            db=db,
            topic="session.revoked",
            payload={
                "session_id": db_session.id,
                "user_id": db_session.user_id
            }
        )

        await db.commit()

        await redis_client.delete(
            self.SESSION_PREFIX + token
        )

    # =========================================
    # REFRESH SESSION
    # =========================================

    async def refresh_session(
        self,
        db: AsyncSession,
        refresh_token: str
    ):

        result = await db.execute(
            select(Session).where(
                Session.refresh_token == refresh_token,
                Session.is_active == True,
                Session.is_revoked == False
            )
        )

        session = result.scalar_one_or_none()

        if not session:
            return None

        if session.refresh_expires_at < datetime.now(timezone.utc):
            return None

        old_session_token = session.session_token

        new_session_token = generate_session_token()
        new_refresh_token = generate_refresh_token()

        await redis_client.delete(
            self.SESSION_PREFIX + old_session_token
        )

        session.session_token = new_session_token
        session.refresh_token = new_refresh_token
        session.last_seen_at = datetime.now(timezone.utc)

        await outbox_service.queue_event(
            db=db,
            topic="session.refreshed",
            payload={
                "session_id": session.id,
                "user_id": session.user_id
            }
        )

        await db.commit()

        await redis_client.set(
            self.SESSION_PREFIX + new_session_token,
            {
                "session_id": session.id,
                "user_id": session.user_id,
                "fingerprint": session.fingerprint
            },
            ttl=settings.SESSION_EXPIRE_SECONDS
        )

        return session

    # =========================================
    # REVOKE USER SESSIONS
    # =========================================

    async def revoke_user_sessions(
        self,
        db: AsyncSession,
        user_id: str
    ):

        result = await db.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.is_active == True
            )
        )

        sessions = result.scalars().all()

        for session in sessions:

            session.is_active = False
            session.is_revoked = True
            session.revoked_at = datetime.now(timezone.utc)

            await redis_client.delete(
                self.SESSION_PREFIX + session.session_token
            )

            await outbox_service.queue_event(
                db=db,
                topic="session.revoked",
                payload={
                    "session_id": session.id,
                    "user_id": session.user_id
                }
            )

        await db.commit()