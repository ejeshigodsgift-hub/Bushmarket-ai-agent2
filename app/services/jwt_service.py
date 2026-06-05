# app/services/jwt_service.py

from datetime import datetime, timedelta, timezone
import jwt

from app.core.config import settings


class JWTService:

    ALGORITHM = "HS256"

    # =========================
    # CREATE ACCESS TOKEN
    # =========================
    def create_access_token(
        self,
        user_id: str,
        roles: list[str],
        session_id: str | None = None,
        cooperative_id: str | None = None,
        expires_minutes: int = 30
    ) -> str:

        now = datetime.now(timezone.utc)

        payload = {
            "sub": user_id,
            "roles": roles,  # shopper | agent | admin
            "session_id": session_id,
            "cooperative_id": cooperative_id,
            "iat": now,
            "exp": now + timedelta(minutes=expires_minutes),
            "type": "access"
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=self.ALGORITHM
        )

    # =========================
    # CREATE REFRESH TOKEN
    # =========================
    def create_refresh_token(
        self,
        user_id: str,
        session_id: str
    ) -> str:

        now = datetime.now(timezone.utc)

        payload = {
            "sub": user_id,
            "session_id": session_id,
            "iat": now,
            "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            "type": "refresh"
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=self.ALGORITHM
        )

    # =========================
    # DECODE TOKEN
    # =========================
    def decode_token(self, token: str) -> dict | None:

        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[self.ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


jwt_service = JWTService()