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


# =========================================
# GENERATE INTERNAL TOKEN
# =========================================
def generate_internal_token(
    service_name: str
):

    now = datetime.now(
        timezone.utc
    )

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

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return token


# =========================================
# VERIFY INTERNAL TOKEN
# =========================================
def verify_internal_token(
    token: str
):

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            audience=AUDIENCE,
            issuer=ISSUER,
            algorithms=[
                settings.JWT_ALGORITHM
            ]
        )

        return payload

    except jwt.ExpiredSignatureError:

        raise HTTPException(
            status_code=401,
            detail="Internal token expired"
        )

    except jwt.InvalidTokenError:

        raise HTTPException(
            status_code=401,
            detail="Invalid internal token"
        )