from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.product_category import ProductCategory

router = APIRouter(prefix="/market/categories", tags=["Categories"])


# =========================
# GET ALL CATEGORIES
# =========================
@router.get("")
async def get_categories(db: AsyncSession = Depends(get_db)):

    stmt = select(ProductCategory).where(
        ProductCategory.is_active.is_(True)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


# =========================
# GET PRODUCTS IN CATEGORY
# =========================
@router.get("/{category_id}/products")
async def get_category_products(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):

    stmt = select(ProductCategory).where(
        ProductCategory.id == category_id
    )

    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        return {"error": "Category not found"}

    products = category.products

    return {
        "category": category.name,
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "image_url": p.image_url
            }
            for p in products
        ]
    }