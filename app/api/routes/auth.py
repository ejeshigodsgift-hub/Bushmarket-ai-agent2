from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.services.rate_limit_service import RateLimitService
from app.services.session_service import SessionService
from app.services.audit_service import AuditService

from app.core.config import settings
from app.core.csrf import generate_csrf_token

from app.schemas.auth import SignupSchema, LoginSchema


router = APIRouter(prefix="/auth", tags=["Auth"])

rate_limit_service = RateLimitService()
session_service = SessionService()
audit_service = AuditService()


# =========================
# SIGNUP
# =========================
@router.post("/signup")
async def signup(
    payload: SignupSchema,
    db: AsyncSession = Depends(get_db)
):

    user = await auth_service.signup(db, payload.dict())

    if not user:
        raise HTTPException(status_code=400, detail="Signup failed")

    return {
        "user_id": user.id,
        "status": "created"
    }


# =========================
# LOGIN
# =========================
@router.post("/login")
async def login(
    payload: LoginSchema,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):

    ip = request.client.host

    # -------------------------
    # RATE LIMIT
    # -------------------------
    await rate_limit_service.check_limit(
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
    result = await auth_service.login(
        db=db,
        identifier=payload.identifier,
        password=payload.password,
        request_meta=meta
    )

    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session = result["session"]

    # =========================
    # SET SESSION COOKIE
    # =========================
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=session.session_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_EXPIRE_SECONDS
    )

    # =========================
    # CSRF TOKEN
    # =========================
    csrf_token = generate_csrf_token()

    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite="strict"
    )

    # =========================
    # AUDIT (LOGIN SUCCESS)
    # =========================
    await audit_service.log(
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
        "session_id": session.id,
        "status": "logged_in"
    }


# =========================
# LOGOUT
# =========================
@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):

    session_token = request.cookies.get(settings.COOKIE_NAME)

    if not session_token:
        return {"status": "logged_out"}

    # =========================
    # GET REAL SESSION
    # =========================
    session = await session_service.get_session_by_token(
        db=db,
        token=session_token
    )

    # =========================
    # AUDIT REAL SESSION
    # =========================
    if session:
        await audit_service.log(
            db=db,
            user_id=session.user_id,
            action="LOGOUT",
            entity_type="session",
            entity_id=session.id,
            metadata={}
        )

    # =========================
    # REVOKE SESSION (DB + REDIS + OUTBOX)
    # =========================
    await session_service.destroy_session(
        db=db,
        token=session_token
    )

    # =========================
    # CLEAR COOKIES
    # =========================
    response.delete_cookie(settings.COOKIE_NAME)
    response.delete_cookie(settings.CSRF_COOKIE_NAME)

    return {
        "status": "logged_out"
    }