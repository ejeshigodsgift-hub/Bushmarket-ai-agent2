from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.services.rate_limit_service import RateLimitService
from app.core.config import settings
from app.core.csrf import generate_csrf_token


router = APIRouter(prefix="/auth")

rate_limit_service = RateLimitService()


# =========================
# SIGNUP
# =========================
@router.post("/signup")
def signup(payload: dict, db: Session = Depends(get_db)):

    user = auth_service.signup(db, payload)

    return {
        "user_id": user.id,
        "status": "created"
    }


# =========================
# LOGIN (SECURE + RATE LIMIT + CSRF + SESSION)
# =========================
@router.post("/login")
def login(
    payload: dict,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):

    # -------------------------
    # 1. RATE LIMITING (anti brute force)
    # -------------------------
    ip = request.client.host

    rate_limit_service.check_limit(
        key=f"login:{ip}",
        limit=5,
        ttl=60
    )

    # -------------------------
    # 2. META DATA (device tracking)
    # -------------------------
    meta = {
        "ip": ip,
        "user_agent": request.headers.get("user-agent")
    }

    # -------------------------
    # 3. AUTHENTICATION
    # -------------------------
    result = auth_service.login(
        db,
        payload["email"],
        payload["password"],
        meta
    )

    if not result:
        return {
            "status": "failed",
            "message": "Invalid credentials"
        }

    # -------------------------
    # 4. SET SESSION COOKIE (PRIMARY AUTH)
    # -------------------------
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=result["session_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24  # 1 day
    )

    # -------------------------
    # 5. CSRF TOKEN (for unsafe requests)
    # -------------------------
    csrf_token = generate_csrf_token()

    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=True,
        samesite="strict"
    )

    # -------------------------
    # 6. RESPONSE
    # -------------------------
    return {
        "user_id": result["user"].id,
        "status": "logged_in"
    }


# =========================
# LOGOUT
# =========================
@router.post("/logout")
def logout(response: Response):

    response.delete_cookie(settings.COOKIE_NAME)
    response.delete_cookie("csrf_token")

    return {
        "status": "logged_out"
    }