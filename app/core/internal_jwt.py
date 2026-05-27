import jwt

from datetime import (
    datetime,
    timedelta
)

from app.core.config import settings


def generate_internal_token(
    service_name: str
):

    payload = {
        "service": service_name,
        "exp": datetime.utcnow() + timedelta(
            minutes=settings.INTERNAL_JWT_EXPIRE_MINUTES
        )
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_internal_token(
    token: str
):

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )