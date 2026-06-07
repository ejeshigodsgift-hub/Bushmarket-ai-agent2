import hashlib
import json

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_product_listing import MarketProductListing
from app.db.models.product import Product
from app.db.models.search_result_cache import SearchResultCache


class SearchService:

    def _make_hash(self, query: str) -> str:
        return hashlib.sha256(query.lower().strip().encode()).hexdigest()

    async def search_products(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 20
    ):
        query_hash = self._make_hash(query)

        # =========================
        # 1. CHECK CACHE FIRST
        # =========================
        cached = await db.execute(
            select(SearchResultCache)
            .where(SearchResultCache.query_hash == query_hash)
        )

        cache_row = cached.scalar_one_or_none()

        if cache_row:
            return json.loads(cache_row.result_json)

        # =========================
        # 2. DB SEARCH
        # =========================
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
        listings = result.scalars().all()

        # =========================
        # 3. STORE CACHE
        # =========================
        cache = SearchResultCache(
            query_hash=query_hash,
            query_text=query,
            result_json=json.dumps([l.id for l in listings]),
            total_results=len(listings)
        )

        db.add(cache)
        await db.commit()

        return listings


search_service = SearchService()