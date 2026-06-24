from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.market_product_listing import MarketProductListing
from app.services.search_service import search_service
from sqlalchemy import select

router = APIRouter(prefix="/market", tags=["Market Listings"])


# =========================
# GET ALL LISTINGS (FILTERS)
# =========================
@router.get("/listings")
async def get_listings(
    market_id: str | None = None,
    category_id: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MarketProductListing).where(
        MarketProductListing.status == "active",
    MarketProductListing.is_active.is_(True)
    )

    if market_id:
        stmt = stmt.where(MarketProductListing.market_id == market_id)

    if min_price is not None:
        stmt = stmt.where(MarketProductListing.unit_price >= min_price)

    if max_price is not None:
        stmt = stmt.where(MarketProductListing.unit_price <= max_price)

    result = await db.execute(stmt)
    listings = result.scalars().all()

    return search_service.to_api_response(listings)


# =========================
# GET SINGLE LISTING
# =========================
@router.get("/listings/{listing_id}")
async def get_listing(listing_id: str, db: AsyncSession = Depends(get_db)):

    stmt = select(MarketProductListing).where(
        MarketProductListing.id == listing_id,
        MarketProductListing.status == "active",
    MarketProductListing.is_active.is_(True)
    )

    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing:
        return {"error": "Listing not found"}

    return search_service.to_api_response([listing])[0]


# =========================
# SEARCH PRODUCTS
# =========================
@router.get("/products/search")
async def search_products(
    q: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):

    listings = await search_service.search_products(
        db=db,
        query=q,
        limit=limit
    )

    return search_service.to_api_response(listings)