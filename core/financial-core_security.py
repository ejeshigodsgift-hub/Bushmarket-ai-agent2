import jwt
from datetime import datetime, timedelta
from fastapi import Request, HTTPException

SECRET = "BUSHMARKET_SECRET"
ALGO = "HS256"


def create_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def get_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "Not authenticated")
    return jwt.decode(token, SECRET, algorithms=[ALGO])