from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.core.config import settings

router = APIRouter(prefix="/auth")


@router.post("/signup")
def signup(payload: dict, db: Session = Depends(get_db)):
    user = auth_service.signup(db, payload)
    return {"user_id": user.id}


@router.post("/login")
def login(payload: dict, response: Response, request: Request, db: Session = Depends(get_db)):

    meta = {
        "ip": request.client.host,
        "user_agent": request.headers.get("user-agent")
    }

    result = auth_service.login(db, payload["email"], payload["password"], meta)

    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=result["session_token"],
        httponly=True,
        secure=True,
        samesite="lax"
    )

    return {"user": result["user"].id}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(settings.COOKIE_NAME)
    return {"message": "logged out"}