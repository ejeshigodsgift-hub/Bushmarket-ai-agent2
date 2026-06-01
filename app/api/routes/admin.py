from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.market_admin_service import MarketAdminService


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

admin_service = MarketAdminService()


# =========================================
# APPROVE AGENT
# =========================================
@router.post("/agent/{user_id}/approve")
async def approve_agent(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    admin_id = request.state.user["id"]

    return await admin_service.approve_agent(
        db=db,
        user_id=user_id,
        admin_id=admin_id
    )


# =========================================
# APPROVE LISTING
# =========================================
@router.post("/listing/{listing_id}/approve")
async def approve_listing(
    listing_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    admin_id = request.state.user["id"]

    return await admin_service.approve_listing(
        db=db,
        listing_id=listing_id,
        admin_id=admin_id
    )