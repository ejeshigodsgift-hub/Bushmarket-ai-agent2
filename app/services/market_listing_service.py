from sqlalchemy.orm import Session

from app.db.models.market_product_listing import (
    MarketProductListing
)


class MarketListingService:

    # =========================
    # CREATE LISTING
    # =========================
    def create_listing(
        self,
        db: Session,
        data: dict
    ):

        listing = MarketProductListing(**data)

        db.add(listing)
        db.commit()
        db.refresh(listing)

        return listing

    # =========================
    # GET MARKET LISTINGS
    # =========================
    def get_market_listings(
        self,
        db: Session,
        market_id: str
    ):

        return db.query(
            MarketProductListing
        ).filter(
            MarketProductListing.market_id == market_id,
            MarketProductListing.is_active == True
        ).all()

    # =========================
    # SEARCH LISTINGS
    # =========================
    def search_market_listings(
        self,
        db: Session,
        keyword: str
    ):

        return db.query(
            MarketProductListing
        ).filter(
            MarketProductListing.title.ilike(f"%{keyword}%"),
            MarketProductListing.is_active == True
        ).all()


market_listing_service = MarketListingService()