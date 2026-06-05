app/services/session_service.py

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.session import Session

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
) -> Session:

    now = datetime.now(timezone.utc)

    fingerprint = generate_device_fingerprint(
        meta.get("ip_address", ""),
        meta.get("user_agent", "")
    )

    session = Session(
        user_id=user_id,
        session_token=generate_session_token(),
        refresh_token=generate_refresh_token(),
        device_id=meta.get("device_id"),
        device_name=meta.get("device_name"),
        user_agent=meta.get("user_agent"),
        ip_address=meta.get("ip_address"),
        fingerprint=fingerprint,

        # Bushmarket Cooperative Context
        cooperative_id=meta.get("cooperative_id"),
        membership_active=meta.get(
            "membership_active",
            False
        ),

        expires_at=now + timedelta(
            seconds=settings.SESSION_EXPIRE_SECONDS
        ),

        refresh_expires_at=now + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        ),

        last_seen_at=now,
        is_active=True,
        is_revoked=False
    )

    db.add(session)

    await db.flush()

    await outbox_service.queue_event(
        db=db,
        topic="session.created",
        payload={
            "session_id": str(session.id),
            "user_id": str(user_id),
            "cooperative_id": session.cooperative_id,
            "membership_active": session.membership_active,
            "device_id": session.device_id
        }
    )

    return session

# =========================================
# GET SESSION
# =========================================

async def get_session(
    self,
    db: AsyncSession,
    token: str,
    ip: str,
    user_agent: str
) -> Session | None:

    result = await db.execute(
        select(Session).where(
            Session.session_token == token,
            Session.is_active.is_(True),
            Session.is_revoked.is_(False)
        )
    )

    session = result.scalar_one_or_none()

    if not session:
        return None

    if session.expires_at < datetime.now(
        timezone.utc
    ):
        return None

    fingerprint = generate_device_fingerprint(
        ip,
        user_agent
    )

    if session.fingerprint != fingerprint:
        return None

    session.last_seen_at = datetime.now(
        timezone.utc
    )

    return session

# =========================================
# GET SESSION BY TOKEN
# =========================================

async def get_session_by_token(
    self,
    db: AsyncSession,
    token: str
) -> Session | None:

    result = await db.execute(
        select(Session).where(
            Session.session_token == token
        )
    )

    return result.scalar_one_or_none()

# =========================================
# REVOKE SESSION
# =========================================

async def revoke_session(
    self,
    db: AsyncSession,
    token: str
) -> None:

    await self.destroy_session(
        db=db,
        token=token
    )

# =========================================
# DESTROY SESSION
# =========================================

async def destroy_session(
    self,
    db: AsyncSession,
    token: str
) -> None:

    result = await db.execute(
        select(Session).where(
            Session.session_token == token
        )
    )

    session = result.scalar_one_or_none()

    if not session:
        return

    session.is_active = False
    session.is_revoked = True
    session.revoked_at = datetime.now(
        timezone.utc
    )

    await outbox_service.queue_event(
        db=db,
        topic="session.revoked",
        payload={
            "session_id": str(session.id),
            "user_id": str(session.user_id)
        }
    )

# =========================================
# REFRESH SESSION
# =========================================

async def refresh_session(
    self,
    db: AsyncSession,
    refresh_token: str
) -> Session | None:

    result = await db.execute(
        select(Session).where(
            Session.refresh_token == refresh_token,
            Session.is_active.is_(True),
            Session.is_revoked.is_(False)
        )
    )

    session = result.scalar_one_or_none()

    if not session:
        return None

    if session.refresh_expires_at < datetime.now(
        timezone.utc
    ):
        return None

    session.session_token = (
        generate_session_token()
    )

    session.refresh_token = (
        generate_refresh_token()
    )

    session.last_seen_at = datetime.now(
        timezone.utc
    )

    await outbox_service.queue_event(
        db=db,
        topic="session.refreshed",
        payload={
            "session_id": str(session.id),
            "user_id": str(session.user_id)
        }
    )

    return session

# =========================================
# REVOKE ALL USER SESSIONS
# =========================================

async def revoke_user_sessions(
    self,
    db: AsyncSession,
    user_id: str
) -> int:

    result = await db.execute(
        select(Session).where(
            Session.user_id == user_id,
            Session.is_active.is_(True)
        )
    )

    sessions = result.scalars().all()

    revoked_count = 0

    for session in sessions:

        session.is_active = False
        session.is_revoked = True

        session.revoked_at = datetime.now(
            timezone.utc
        )

        await outbox_service.queue_event(
            db=db,
            topic="session.revoked",
            payload={
                "session_id": str(session.id),
                "user_id": str(session.user_id)
            }
        )

        revoked_count += 1

    return revoked_count

session_service = SessionService()