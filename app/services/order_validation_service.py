from fastapi import HTTPException

from app.db.models.market_product_listing import MarketProductListing


class OrderValidationService:

    VALID_STATUSES = [
        "active"
    ]

    def validate_listing_for_checkout(
        self,
        listing: MarketProductListing,
        quantity: int
    ):

        if not listing:
            raise HTTPException(
                status_code=404,
                detail="Listing not found"
            )

        if listing.status not in self.VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Listing unavailable"
            )

        if listing.available_stock <= 0:
            raise HTTPException(
                status_code=400,
                detail="Out of stock"
            )

        if quantity > listing.available_stock:
            raise HTTPException(
                status_code=400,
                detail="Insufficient stock"
            )

        if listing.unit_price <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid pricing"
            )