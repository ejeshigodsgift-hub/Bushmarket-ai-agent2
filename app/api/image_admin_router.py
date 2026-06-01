from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.image_approval_service import image_approval_service


router = APIRouter(prefix="/admin/images", tags=["Image Admin"])


# =========================
# APPROVE PRODUCT IMAGE
# =========================
@router.post("/product/{product_id}/approve")
async def approve_product(product_id: str, db: AsyncSession = Depends(get_db)):

    return await image_approval_service.approve_product_image(db, product_id)


# =========================
# REJECT PRODUCT IMAGE
# =========================
@router.post("/product/{product_id}/reject")
async def reject_product(product_id: str, db: AsyncSession = Depends(get_db)):

    return await image_approval_service.reject_product_image(db, product_id)


# =========================
# APPROVE CATEGORY IMAGE
# =========================
@router.post("/category/{category_id}/approve")
async def approve_category(category_id: str, db: AsyncSession = Depends(get_db)):

    return await image_approval_service.approve_category_image(db, category_id)