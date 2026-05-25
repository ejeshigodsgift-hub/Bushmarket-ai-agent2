from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.market_listing_service import (
    market_listing_service
)

router = APIRouter(prefix="/listings")


# =========================
# GET MARKET LISTINGS
# =========================
@router.get("/market/{market_id}")
def get_market_listings(
    market_id: str,
    db: Session = Depends(get_db)
):

    return db.query(MarketProductListing).filter(
        MarketProductListing.market_id == market_id,
        MarketProductListing.status == "active",
        MarketProductListing.is_active == True
    ).all()


# =========================
# SEARCH LISTINGS
# =========================
@router.get("/search")
def search_listings(
    keyword: str,
    db: Session = Depends(get_db)
):

    return market_listing_service.search_market_listings(
        db,
        keyword
    )