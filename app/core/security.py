import bcrypt
import secrets
import hashlib
import hmac

from app.core.config import settings


# =========================================
# PASSWORD SECURITY (SYNC but isolated)
# =========================================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        password.encode(),
        hashed.encode()
    )


# =========================================
# TOKENS
# =========================================
def generate_session_token() -> str:
    return secrets.token_urlsafe(64)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


# =========================================
# API KEYS
# =========================================
def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(raw_key: str, hashed_key: str) -> bool:
    return hmac.compare_digest(
        hash_api_key(raw_key),
        hashed_key
    )


# =========================================
# DEVICE FINGERPRINT
# =========================================
def generate_device_fingerprint(ip: str, user_agent: str) -> str:
    raw = f"{ip}:{user_agent}"
    return hashlib.sha256(raw.encode()).hexdigest()