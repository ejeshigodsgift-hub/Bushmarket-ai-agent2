from app.integrations.redis_client import redis_client
from app.core.security import generate_session_token, generate_refresh_token
import json
import secrets


class SessionService:

    SESSION_PREFIX = "session:"

    # =========================
    # CREATE SESSION (LOGIN)
    # =========================
    def create_session(self, user_id: str, meta: dict):

        session_token = generate_session_token()
        refresh_token = generate_refresh_token()

        session_data = {
            "user_id": user_id,
            "refresh_token": refresh_token,
            "meta": meta
        }

        redis_client.set(
            self.SESSION_PREFIX + session_token,
            json.dumps(session_data),
            ttl=60 * 60 * 24
        )

        return session_token, refresh_token

    # =========================
    # GET SESSION (AUTH CHECK)
    # =========================
    def get_session(self, token: str):
        data = redis_client.get(self.SESSION_PREFIX + token)
        return json.loads(data) if data else None

    # =========================
    # DESTROY SESSION (LOGOUT)
    # =========================
    def destroy_session(self, token: str):
        redis_client.set(self.SESSION_PREFIX + token, "", ttl=1)

    # =========================
    # REFRESH SESSION (SECURITY ROTATION)
    # =========================
    def refresh_session(self, session_token: str):

        existing = redis_client.get(self.SESSION_PREFIX + session_token)

        if not existing:
            return None

        data = json.loads(existing)

        new_token = secrets.token_urlsafe(64)

        redis_client.set(
            self.SESSION_PREFIX + new_token,
            json.dumps(data),
            ttl=60 * 60 * 24
        )

        # invalidate old session
        redis_client.set(self.SESSION_PREFIX + session_token, "", ttl=1)

        return new_token