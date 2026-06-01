from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.product import Product
from app.db.models.product_category import ProductCategory


class ImageApprovalService:

    # =========================
    # APPROVE PRODUCT IMAGE
    # =========================
    async def approve_product_image(
        self,
        db: AsyncSession,
        product_id: str
    ):

        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )

        product = result.scalar_one_or_none()

        if not product:
            return None

        product.image_status = "approved"

        await db.commit()
        return product

    # =========================
    # REJECT PRODUCT IMAGE
    # =========================
    async def reject_product_image(
        self,
        db: AsyncSession,
        product_id: str
    ):

        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )

        product = result.scalar_one_or_none()

        if not product:
            return None

        product.image_status = "rejected"

        await db.commit()
        return product

    # =========================
    # APPROVE CATEGORY IMAGE
    # =========================
    async def approve_category_image(
        self,
        db: AsyncSession,
        category_id: str
    ):

        result = await db.execute(
            select(ProductCategory).where(ProductCategory.id == category_id)
        )

        category = result.scalar_one_or_none()

        if not category:
            return None

        category.image_status = "approved"

        await db.commit()
        return category


image_approval_service = ImageApprovalService()