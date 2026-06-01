from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.services.product_category_service import product_category_service
from app.services.category_visibility_service import category_visibility_service
from app.services.product_visibility_service import product_visibility_service


router = APIRouter(
    prefix="/categories",
    tags=["Product Categories"]
)


# ====================================================
# GET ALL CATEGORIES
# ====================================================
@router.get("/")
async def get_categories(db: AsyncSession = Depends(get_db)):

    categories = await product_category_service.get_all(db)

    return [
        {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "image_url": category_visibility_service.apply_visibility(category).image_url
        }
        for category in categories
    ]


# ====================================================
# GET CATEGORY WITH PRODUCTS
# ====================================================
@router.get("/{slug}")
async def get_category(slug: str, db: AsyncSession = Depends(get_db)):

    category = await product_category_service.get_category_products(db, slug)

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Apply visibility rule for category image
    category = category_visibility_service.apply_visibility(category)

    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "image_url": category.image_url,

        "products": [
            {
                "id": product.id,
                "name": product.name,
                "slug": product.slug,
                "image_url": product_visibility_service.apply_visibility(product).image_url,
                "base_price": product.base_price,
                "is_active": product.is_active
            }
            for product in category.products
        ]
    }