# =========================================
# FILE: app/services/product_service.py
# =========================================

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from app.db.models.products import Product


class ProductService:

    # =========================================
    # SEARCH PRODUCTS
    # =========================================
    async def search_products(
        self,
        db: AsyncSession,
        keyword: str
    ):

        stmt = (
            select(Product)
            .where(
                Product.is_active.is_(True),
                or_(
                    Product.name.ilike(f"%{keyword}%"),
                    Product.slug.ilike(f"%{keyword}%")
                )
            )
            .order_by(Product.name.asc())
            .limit(100)
        )

        result = await db.execute(stmt)

        return result.scalars().all()

    # =========================================
    # GET PRODUCT
    # =========================================
    async def get_product(
        self,
        db: AsyncSession,
        product_id: str
    ) -> Product:

        stmt = (
            select(Product)
            .where(
                Product.id == product_id,
                Product.is_active.is_(True)
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        return product

    # =========================================
    # CREATE PRODUCT
    # =========================================
    async def create_product(
        self,
        db: AsyncSession,
        payload: dict
    ) -> Product:

        existing_stmt = (
            select(Product)
            .where(
                Product.slug == payload["slug"]
            )
            .limit(1)
        )

        existing_result = await db.execute(existing_stmt)

        existing = existing_result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Product slug already exists"
            )

        product = Product(
            name=payload["name"],
            slug=payload["slug"],
            description=payload.get("description"),
            category_id=payload.get("category_id"),
            is_active=True
        )

        db.add(product)

        await db.commit()

        await db.refresh(product)

        return product


product_service = ProductService()