import secrets
from fastapi import Request, HTTPException


CSRF_HEADER = "x-csrf-token"


def generate_csrf_token():
    return secrets.token_urlsafe(32)


def validate_csrf(request: Request):

    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get(CSRF_HEADER)

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