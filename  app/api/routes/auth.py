from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.rate_limit_service import RateLimitService
from app.services.auth_service import auth_service
from app.core.csrf import generate_csrf_token


router = APIRouter(prefix="/auth")

rate_limit_service = RateLimitService()


@router.post("/login")
def login(
    payload: dict,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):

    ip = request.client.host

    rate_limit_service.check_limit(
        key=f"login:{ip}"
    )

    meta = {
        "ip": ip,
        "user_agent": request.headers.get("user-agent")
    }

    result = auth_service.login(
        db,
        payload["email"],
        payload["password"],
        meta
    )

    csrf_token = generate_csrf_token()

    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=True,
        samesite="strict"
    )

    return {
        "user_id": result["user"].id
    }