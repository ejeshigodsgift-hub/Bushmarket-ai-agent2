from fastapi import HTTPException

from app.db.models.market_product_listing import MarketProductListing


class CartValidationService:

    def validate_listing_for_cart(
        self,
        listing: MarketProductListing
    ):

        if not listing:
            raise HTTPException(
                status_code=404,
                detail="Listing not found"
            )

        if listing.status != "active":
            raise HTTPException(
                status_code=400,
                detail="Listing inactive"
            )

        if listing.available_stock <= 0:
            raise HTTPException(
                status_code=400,
                detail="Out of stock"
            )

        if listing.unit_price <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid price"
            )

        if not listing.measurement_unit_id:
            raise HTTPException(
                status_code=400,
                detail="Measurement unit missing"
            )

        if not listing.market_id:
            raise HTTPException(
                status_code=400,
                detail="Market missing"
            )