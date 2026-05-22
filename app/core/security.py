import bcrypt
import secrets
import hashlib
import hmac
from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def generate_session_token() -> str:
    return secrets.token_urlsafe(64)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()