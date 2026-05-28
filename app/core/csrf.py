import hmac
import secrets
import hashlib

from fastapi import (
    Request,
    HTTPException
)

from app.core.config import settings


CSRF_HEADER = settings.CSRF_HEADER_NAME


# =========================================
# GENERATE CSRF TOKEN
# =========================================
def generate_csrf_token():

    raw = secrets.token_urlsafe(32)

    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        raw.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{raw}.{signature}"


# =========================================
# VALIDATE CSRF TOKEN
# =========================================
def validate_csrf(request: Request):

    csrf_cookie = request.cookies.get(
        settings.CSRF_COOKIE_NAME
    )

    csrf_header = request.headers.get(
        CSRF_HEADER
    )

    if not csrf_cookie or not csrf_header:

        raise HTTPException(
            status_code=403,
            detail="CSRF token missing"
        )

    if csrf_cookie != csrf_header:

        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )

    try:

        raw, signature = csrf_cookie.split(".")

    except ValueError:

        raise HTTPException(
            status_code=403,
            detail="Malformed CSRF token"
        )

    expected_signature = hmac.new(
        settings.SECRET_KEY.encode(),
        raw.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        signature,
        expected_signature
    ):

        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF signature"
        )