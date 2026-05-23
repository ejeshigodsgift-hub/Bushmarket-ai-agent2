import json
import secrets

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session as DBSession

from app.db.models.session import Session
from app.integrations.redis_client import redis_client

from app.core.security import (
    generate_session_token,
    generate_refresh_token
)

from app.core.config import settings


class SessionService:

    SESSION_PREFIX = "session:"

    # =========================
    # CREATE SESSION
    # =========================

    def create_session(
        self,
        db: DBSession,
        user_id: str,
        meta: dict
    ):

        session_token = generate_session_token()

        refresh_token = generate_refresh_token()

        now = datetime.now(timezone.utc)

        expires_at = now + timedelta(
            seconds=settings.SESSION_EXPIRE_SECONDS
        )

        refresh_expires_at = now + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        # =========================
        # POSTGRESQL PERSISTENCE
        # =========================

        db_session = Session(
            user_id=user_id,

            session_token=session_token,
            refresh_token=refresh_token,

            device_id=meta.get("device_id"),
            device_name=meta.get("device_name"),

            user_agent=meta.get("user_agent"),
            ip_address=meta.get("ip_address"),

            expires_at=expires_at,
            refresh_expires_at=refresh_expires_at,

            is_active=True,
            is_revoked=False,

            last_seen_at=now
        )

        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        # =========================
        # REDIS CACHE
        # =========================

        session_data = {
            "session_id": db_session.id,
            "user_id": user_id,
            "device_id": db_session.device_id,
            "is_revoked": False
        }

        redis_client.set(
            self.SESSION_PREFIX + session_token,
            session_data,
            ttl=settings.SESSION_EXPIRE_SECONDS
        )

        return db_session

    # =========================
    # GET SESSION
    # =========================

    def get_session(
        self,
        db: DBSession,
        token: str
    ):

        # =========================
        # REDIS FAST LOOKUP
        # =========================

        cached = redis_client.get(
            self.SESSION_PREFIX + token
        )

        if cached:

            db_session = db.query(Session).filter(
                Session.session_token == token,
                Session.is_active == True,
                Session.is_revoked == False
            ).first()

            if db_session:
                db_session.last_seen_at = datetime.now(timezone.utc)
                db.commit()

            return db_session

        # =========================
        # POSTGRESQL FALLBACK
        # =========================

        db_session = db.query(Session).filter(
            Session.session_token == token,
            Session.is_active == True,
            Session.is_revoked == False
        ).first()

        if not db_session:
            return None

        if db_session.expires_at < datetime.now(timezone.utc):
            return None

        # =========================
        # REHYDRATE REDIS
        # =========================

        redis_client.set(
            self.SESSION_PREFIX + token,
            {
                "session_id": db_session.id,
                "user_id": db_session.user_id
            },
            ttl=settings.SESSION_EXPIRE_SECONDS
        )

        db_session.last_seen_at = datetime.now(timezone.utc)

        db.commit()

        return db_session

    # =========================
    # DESTROY SESSION
    # =========================

    def destroy_session(
        self,
        db: DBSession,
        token: str
    ):

        db_session = db.query(Session).filter(
            Session.session_token == token
        ).first()

        if not db_session:
            return

        db_session.is_active = False
        db_session.is_revoked = True
        db_session.revoked_at = datetime.now(timezone.utc)

        db.commit()

        redis_client.delete(
            self.SESSION_PREFIX + token
        )

    # =========================
    # REFRESH SESSION
    # =========================

    def refresh_session(
        self,
        db: DBSession,
        refresh_token: str
    ):

        existing = db.query(Session).filter(
            Session.refresh_token == refresh_token,
            Session.is_active == True,
            Session.is_revoked == False
        ).first()

        if not existing:
            return None

        if existing.refresh_expires_at < datetime.now(timezone.utc):
            return None

        # =========================
        # ROTATE TOKENS
        # =========================

        new_session_token = generate_session_token()

        new_refresh_token = generate_refresh_token()

        existing.session_token = new_session_token
        existing.refresh_token = new_refresh_token

        existing.last_seen_at = datetime.now(timezone.utc)

        db.commit()

        # =========================
        # REDIS CACHE UPDATE
        # =========================

        redis_client.set(
            self.SESSION_PREFIX + new_session_token,
            {
                "session_id": existing.id,
                "user_id": existing.user_id
            },
            ttl=settings.SESSION_EXPIRE_SECONDS
        )

        return existing

    # =========================
    # REVOKE ALL USER SESSIONS
    # =========================

    def revoke_user_sessions(
        self,
        db: DBSession,
        user_id: str
    ):

        sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.is_active == True
        ).all()

        for session in sessions:

            session.is_active = False
            session.is_revoked = True
            session.revoked_at = datetime.now(timezone.utc)

            redis_client.delete(
                self.SESSION_PREFIX + session.session_token
            )

        db.commit()