from app.integrations.redis_client import redis_client
from app.core.security import generate_session_token, generate_refresh_token
import json


SESSION_PREFIX = "session:"
USER_SESSION_INDEX = "user_sessions:"


class SessionService:

    def create_session(self, user_id: str, meta: dict):
        session_token = generate_session_token()
        refresh_token = generate_refresh_token()

        session_data = {
            "user_id": user_id,
            "refresh_token": refresh_token,
            "meta": meta
        }

        redis_client.set(
            SESSION_PREFIX + session_token,
            json.dumps(session_data),
            ttl=60 * 60 * 24  # 1 day
        )

        return session_token, refresh_token

    def get_session(self, token: str):
        data = redis_client.get(SESSION_PREFIX + token)
        return json.loads(data) if data else None

    def destroy_session(self, token: str):
        redis_client.set(SESSION_PREFIX + token, "", ttl=1)