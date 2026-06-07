from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_product_listing import MarketProductListing
from app.db.models.product import Product


class SearchService:

    async def search_products(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 20
    ):
        stmt = (
            select(MarketProductListing)
            .join(Product)
            .where(
                or_(
                    Product.name.ilike(f"%{query}%"),
                    Product.description.ilike(f"%{query}%"),
                    MarketProductListing.title.ilike(f"%{query}%"),
                ),
                MarketProductListing.is_active.is_(True)
            )
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()


search_service = SearchService()