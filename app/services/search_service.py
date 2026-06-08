import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.market_product_listing import MarketProductListing
from app.db.models.product import Product
from app.db.models.search_query import SearchQuery
from app.db.models.search_result_cache import SearchResultCache


class SearchService:

    # =========================
    # HASH NORMALIZATION
    # =========================
    def _make_hash(self, query: str) -> str:
        return hashlib.sha256(
            query.lower().strip().encode()
        ).hexdigest()

    # =========================
    # CORE SEARCH ENGINE
    # =========================
    async def search_products(
        self,
        db: AsyncSession,
        query: str,
        user_id: str | None = None,
        limit: int = 20
    ):

        normalized_query = query.lower().strip()
        query_hash = self._make_hash(query)

        # =====================================================
        # 1. CACHE LOOKUP (FAST PATH)
        # =====================================================
        cache_stmt = (
            select(SearchResultCache)
            .where(SearchResultCache.query_hash == query_hash)
        )

        cache_result = await db.execute(cache_stmt)
        cache_row = cache_result.scalar_one_or_none()

        if cache_row:
            return json.loads(cache_row.result_json)

        # =====================================================
        # 2. DATABASE SEARCH (SLOW PATH)
        # =====================================================
        stmt = (
            select(MarketProductListing)
            .options(
                selectinload(MarketProductListing.product),
                selectinload(MarketProductListing.market),
                selectinload(MarketProductListing.inventory),
            )
            .join(Product)
            .where(
                or_(
                    Product.name.ilike(f"%{normalized_query}%"),
                    Product.description.ilike(f"%{normalized_query}%"),
                    MarketProductListing.title.ilike(f"%{normalized_query}%"),
                ),
                MarketProductListing.is_active.is_(True),
                MarketProductListing.status == "active"
            )
            .limit(limit)
        )

        result = await db.execute(stmt)
        listings = result.scalars().unique().all()

        # =====================================================
        # 3. LOG SEARCH QUERY (AI + ANALYTICS LAYER)
        # =====================================================
        if user_id:
            search_log = SearchQuery(
                user_id=user_id,
                query_text=query,
                normalized_query=normalized_query,
                total_results=len(listings),
                search_source="manual"
            )
            db.add(search_log)

        # =====================================================
        # 4. SERIALIZE RESULTS (CACHE FORMAT)
        # =====================================================
        serialized = [
            {
                "listing_id": l.id,
                "product_name": l.product.name,
                "image_url": l.product.image_url,
                "unit_price": str(l.unit_price),
                "market_name": l.market.market_name,
                "availability": l.available_stock
            }
            for l in listings
        ]

        # =====================================================
        # 5. STORE CACHE (FAST REUSE LAYER)
        # =====================================================
        cache_entry = SearchResultCache(
            query_hash=query_hash,
            query_text=query,
            result_json=json.dumps(serialized),
            total_results=len(serialized),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
        )

        db.add(cache_entry)

        # commit once (optimized)
        await db.commit()

        return serialized


search_service = SearchService()