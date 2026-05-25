from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.services.market_listing_service import (
    market_listing_service
)

from app.services.permission_service import (
    PermissionService
)

router = APIRouter(prefix="/admin/listings")

permission_service = PermissionService()


# =========================
# CREATE LISTING
# =========================
@router.post("/")
def create_listing(
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

    listing = market_listing_service.create_listing(
        db,
        payload
    )

    return {
        "listing_id": listing.id
    }