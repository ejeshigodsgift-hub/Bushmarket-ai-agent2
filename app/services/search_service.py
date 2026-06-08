# =========================================
# FILE: app/services/search_service.py
# =========================================

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
from app.db.models.market_location import MarketLocation


class SearchService:

    # =========================
    # HASH NORMALIZATION
    # =========================
    def _make_hash(self, query: str) -> str:
        return hashlib.sha256(
            query.lower().strip().encode()
        ).hexdigest()

    # =========================
    # SERIALIZER
    # =========================
    def to_api_response(self, listings):

        return [
            {
                "listing_id": listing.id,
                "product_name": listing.product.name,
                "image_url": listing.product.image_url,
                "unit_price": float(listing.unit_price),
                "market": {
                    "id": listing.market.id,
                    "name": listing.market.market_name
                },
                "availability": listing.available_stock
            }
            for listing in listings
        ]

    # =========================
    # CORE SEARCH ENGINE
    # =========================
    async def search_products(
        self,
        db: AsyncSession,
        query: str,
        user_id: str | None = None,
        user_lat: float | None = None,
        user_lng: float | None = None,
        limit: int = 20
    ):
        normalized_query = query.lower().strip()
        query_hash = self._make_hash(query)

        # =====================================================
        # DATABASE SEARCH
        # =====================================================
        stmt = (
            select(MarketProductListing)
            .options(
                selectinload(MarketProductListing.product),
                selectinload(MarketProductListing.market),
                selectinload(MarketProductListing.inventory),
            )
            .join(Product)
            .join(MarketLocation)
            .where(
                or_(
                    Product.name.ilike(f"%{normalized_query}%"),
                    Product.description.ilike(f"%{normalized_query}%"),
                    MarketProductListing.title.ilike(f"%{normalized_query}%"),
                    MarketLocation.market_name.ilike(f"%{normalized_query}%")
                ),
                MarketProductListing.is_active.is_(True),
                MarketProductListing.status == "active"
            )
            .limit(limit)
        )

        # =========================
        # NEAREST MARKET SUPPORT
        # =========================
        if user_lat is not None and user_lng is not None:
            stmt = stmt.order_by(
                MarketLocation.latitude - user_lat,
                MarketLocation.longitude - user_lng
            )

        result = await db.execute(stmt)
        listings = result.scalars().unique().all()

        # =====================================================
        # SEARCH ANALYTICS
        # =====================================================
        if user_id:
            db.add(
                SearchQuery(
                    user_id=user_id,
                    query_text=query,
                    normalized_query=normalized_query,
                    total_results=len(listings),
                    search_source="manual"
                )
            )

        # =====================================================
        # CACHE SERIALIZED VERSION
        # =====================================================
        serialized = self.to_api_response(listings)

        cache_stmt = (
            select(SearchResultCache)
            .where(SearchResultCache.query_hash == query_hash)
        )

        cache_result = await db.execute(cache_stmt)
        existing_cache = cache_result.scalar_one_or_none()

        if existing_cache:
            existing_cache.result_json = json.dumps(serialized)
            existing_cache.total_results = len(serialized)
            existing_cache.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        else:
            db.add(
                SearchResultCache(
                    query_hash=query_hash,
                    query_text=query,
                    result_json=json.dumps(serialized),
                    total_results=len(serialized),
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
                )
            )

        await db.commit()

        # =====================================================
        # RETURN ORM OBJECTS FOR AI + BUSINESS LOGIC
        # =====================================================
        return listings


search_service = SearchService()