from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.market_service import market_service
from app.services.search_service import search_service
from app.db.models.product import Product
from app.db.models.market_product_listing import MarketProductListing

router = APIRouter(prefix="/markets", tags=["Markets"])


# =========================
# GET ALL MARKETS
# =========================
@router.get("")
async def get_markets(db: AsyncSession = Depends(get_db)):
    return await market_service.get_markets(db)


# =========================
# GET MARKET DETAILS
# =========================
@router.get("/{market_id}")
async def get_market(market_id: str, db: AsyncSession = Depends(get_db)):
    return await market_service.get_market_by_id(db, market_id)