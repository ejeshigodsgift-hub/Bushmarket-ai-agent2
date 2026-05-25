from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.market_service import market_service
from app.services.permission_service import PermissionService


router = APIRouter(prefix="/admin/markets")

permission_service = PermissionService()


# =========================
# CREATE MARKET
# =========================
@router.post("/")
def create_market(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(status_code=401)

    permission_service.validate_permission(
        user.get("roles", []),
        "*"
    )

    market = market_service.create_market(
        db,
        payload
    )

    return {
        "market_id": market.id
    }