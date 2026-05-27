import uuid
import jwt

from datetime import (
    datetime,
    timedelta,
    timezone
)

from fastapi import HTTPException

from app.core.config import settings


ISSUER = "bushmarket-auth"
AUDIENCE = "internal-services"


def generate_internal_token(service_name: str):

    now = datetime.now(timezone.utc)

    payload = {
        "jti": str(uuid.uuid4()),
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": service_name,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(
            minutes=settings.INTERNAL_JWT_EXPIRE_MINUTES
        )
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_internal_token(token: str):

    try:

        return jwt.decode(
            token,
            settings.SECRET_KEY,
            audience=AUDIENCE,
            issuer=ISSUER,
            algorithms=[settings.JWT_ALGORITHM]
        )

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid internal token"
        )