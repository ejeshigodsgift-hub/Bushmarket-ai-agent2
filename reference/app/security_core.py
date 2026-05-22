from passlib.context import CryptContext
import secrets
import hashlib
import hmac
import time
import jwt
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =========================
# PASSWORD HASHING
# =========================
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


# =========================
# COOKIE SESSION TOKEN
# =========================
def generate_session_token() -> str:
    return secrets.token_urlsafe(64)


# =========================
# INTERNAL JWT (SERVICE TO SERVICE)
# =========================
def create_internal_jwt(payload: dict) -> str:
    payload["iat"] = int(time.time())
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_internal_jwt(token: str):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


# =========================
# API KEY SIGNING (SUPPLIERS)
# =========================
def generate_api_key() -> str:
    return secrets.token_urlsafe(48)


def sign_api_key(api_key: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(),
        api_key.encode(),
        hashlib.sha256
    ).hexdigest()