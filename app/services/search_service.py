# =========================================
# FILE: app/services/search_service.py
# =========================================

import hashlib
import json
from app.db.models.cooperative_demand_signal import CooperativeDemandSignal
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, or_, func, cast, Float
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
        # BASE QUERY
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
        )

        # =====================================================
        # NEAREST MARKET (HAVERSINE FORMULA)
        # =====================================================
        if user_lat is not None and user_lng is not None:

            lat = func.radians(MarketLocation.latitude)
            lng = func.radians(MarketLocation.longitude)
            user_lat_rad = func.radians(user_lat)
            user_lng_rad = func.radians(user_lng)

            dlat = lat - user_lat_rad
            dlng = lng - user_lng_rad

            a = (
                func.pow(func.sin(dlat / 2), 2)
                + func.cos(user_lat_rad)
                * func.cos(lat)
                * func.pow(func.sin(dlng / 2), 2)
            )

            c = 2 * func.atan2(func.sqrt(a), func.sqrt(1 - a))

            earth_radius_km = 6371

            distance_expr = earth_radius_km * c

            stmt = stmt.order_by(distance_expr)

        # apply limit AFTER ordering
        stmt = stmt.limit(limit)

        # =====================================================
        # EXECUTE QUERY
        # =====================================================
        result = await db.execute(stmt)
        listings = result.scalars().unique().all()

        # =====================================================
        # SEARCH ANALYTICS
        # =====================================================
        if user_id:

            first_listing = listings[0]  if listings else None
            first_product = (
                first_listing.product
                if first_listing
                else None
            )

            db.add(
                SearchQuery(
                    user_id=user_id,
                    query_text=query,
              normalized_query=normalized_query,
                    total_results=len(listings),
                    search_source="manual",
                    product_id=(
                        first_product.id
                        if first_product
                        else None
                    )
                )
            )

            if first_listing and first_product:
                db.add(
                    CooperativeDemandSignal(
                 product_id=first_product.id,
                market_id=first_listing.market_id,
                        user_id=user_id,
                        signal_type="search"
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

        return listings


search_service = SearchService()