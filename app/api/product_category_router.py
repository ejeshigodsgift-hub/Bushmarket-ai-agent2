from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.product_category_service import product_category_service


router = APIRouter(prefix="/categories", tags=["Categories"])


# ====================================================
# GET ALL CATEGORIES (HOME / BROWSE PAGE)
# ====================================================
@router.get("/")
async def get_categories(db: AsyncSession = Depends(get_db)):

    categories = await product_category_service.get_all(db)

    return [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "image_url": c.image_url
        }
        for c in categories
    ]


# ====================================================
# GET SINGLE CATEGORY + PRODUCTS
# ====================================================
@router.get("/{slug}")
async def get_category(slug: str, db: AsyncSession = Depends(get_db)):

    category = await product_category_service.get_category_products(db, slug)

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
        "image_url": category.image_url,

        # PRODUCTS INSIDE CATEGORY
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "image_url": p.image_url,
                "base_price": p.base_price
            }
            for p in category.products
        ]
    }