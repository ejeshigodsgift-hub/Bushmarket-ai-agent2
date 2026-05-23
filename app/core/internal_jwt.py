import jwt
from datetime import datetime, timedelta
from app.core.config import settings


def generate_internal_token(service_name: str):

    payload = {
        "service": service_name,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256"
    )


def verify_internal_token(token: str):

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"]
    )