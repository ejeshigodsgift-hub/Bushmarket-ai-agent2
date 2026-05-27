from fastapi import HTTPException


class CheckoutValidationService:

    def validate_cart(self, cart):

        if not cart:
            raise HTTPException(404, "Cart not found")

        if not cart.items:
            raise HTTPException(400, "Cart is empty")

        for item in cart.items:

            listing = item.listing

            if listing.status != "active":
                raise HTTPException(400, "Inactive listing")

            if listing.available_stock < item.quantity:
                raise HTTPException(400, "Insufficient stock")

            if listing.unit_price <= 0:
                raise HTTPException(400, "Invalid price")

            if not listing.measurement_unit_id:
                raise HTTPException(400, "Missing measurement unit")

            if not listing.market_id:
                raise HTTPException(400, "Missing market location")