from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.services.rate_limit_service import RateLimitService
from app.services.session_service import SessionService
from app.services.audit_service import AuditService

from app.core.config import settings
from app.core.csrf import generate_csrf_token


router = APIRouter(prefix="/auth")

rate_limit_service = RateLimitService()
session_service = SessionService()
audit_service = AuditService()


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
# LOGIN (FULL HYBRID SESSION)
# =========================
@router.post("/login")
def login(
    payload: dict,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):

    ip = request.client.host

    # -------------------------
    # RATE LIMIT
    # -------------------------
    rate_limit_service.check_limit(
        key=f"login:{ip}",
        limit=5,
        ttl=60
    )

    # -------------------------
    # DEVICE META
    # -------------------------
    meta = {
        "ip_address": ip,
        "user_agent": request.headers.get("user-agent"),
        "device_id": request.headers.get("x-device-id"),
        "device_name": request.headers.get("x-device-name")
    }

    # -------------------------
    # AUTH LOGIN
    # -------------------------
    result = auth_service.login(
        db,
        payload["email"],
        payload["password"],
        meta
    )

    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session = result["session"]

    # -------------------------
    # SESSION COOKIE
    # -------------------------
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=session.session_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_EXPIRE_SECONDS
    )

    # -------------------------
    # CSRF TOKEN
    # -------------------------
    csrf_token = generate_csrf_token()

    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite="strict"
    )

    # -------------------------
    # AUDIT LOG
    # -------------------------
    audit_service.log(
        db=db,
        user_id=session.user_id,
        action="LOGIN_SUCCESS",
        entity_type="session",
        entity_id=session.id,
        metadata={
            "ip": ip,
            "device_id": meta.get("device_id")
        }
    )

    return {
        "user_id": result["user"].id,
        "status": "logged_in"
    }


# =========================
# LOGOUT (FULL REVOCATION)
# =========================
@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):

    session_token = request.cookies.get(settings.COOKIE_NAME)

    if session_token:

        session_service.revoke_session(
            db=db,
            token=session_token
        )

        audit_service.log(
            db=db,
            user_id="unknown",
            action="LOGOUT",
            entity_type="session",
            entity_id=session_token,
            metadata={}
        )

    response.delete_cookie(settings.COOKIE_NAME)
    response.delete_cookie(settings.CSRF_COOKIE_NAME)

    return {
        "status": "logged_out"
    }