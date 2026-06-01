from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.product_category import ProductCategory


class ProductCategoryService:

    # =========================
    # GET ALL ACTIVE CATEGORIES
    # =========================
    async def get_all(self, db: AsyncSession):

        result = await db.execute(
            select(ProductCategory)
            .where(ProductCategory.is_active == True)
            .order_by(ProductCategory.sort_order.asc())
        )

        return result.scalars().all()

    # =========================
    # GET SINGLE CATEGORY (by slug)
    # =========================
    async def get_by_slug(self, db: AsyncSession, slug: str):

        result = await db.execute(
            select(ProductCategory).where(
                ProductCategory.slug == slug,
                ProductCategory.is_active == True
            )
        )

        return result.scalar_one_or_none()

    # =========================
    # GET CATEGORY WITH PRODUCTS
    # =========================
    async def get_category_products(self, db: AsyncSession, slug: str):

        category = await self.get_by_slug(db, slug)

        if not category:
            return None

        # lazy-loaded via relationship (ProductCategory.products)
        return category


product_category_service = ProductCategoryService()