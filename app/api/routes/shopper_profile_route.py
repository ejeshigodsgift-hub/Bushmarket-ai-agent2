from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.shopper_profile_service import shopper_profile_service
from app.schemas.shopper_profile import ShopperProfileUpdateSchema


router = APIRouter(prefix="/shopper-profile", tags=["Shopper Profile"])


# ====================================================
# GET SHOPPER PROFILE
# ====================================================
@router.get("/")
async def get_profile(
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    profile = await shopper_profile_service.get_profile(
        db=db,
        user_id=user["id"]
    )

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "user_id": user["id"],
        "location": profile.location,
        "preferred_categories": profile.preferred_categories,
        "created_at": profile.created_at
    }


# ====================================================
# UPDATE SHOPPER PROFILE (UPGRADE FLOW)
# ====================================================
@router.patch("/")
async def update_profile(
    payload: ShopperProfileUpdateSchema,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    updated = await shopper_profile_service.update_profile(
        db=db,
        user_id=user["id"],
        data=payload.model_dump(exclude_unset=True)
    )

    return {
        "status": "updated",
        "user_id": user["id"],
        "profile": {
            "location": updated.location,
            "preferred_categories": updated.preferred_categories,
            "updated_at": updated.updated_at
        }
    }