from decimal import Decimal
from dataclasses import asdict

from app.db.models.pricing_model.py import PriceBreakdown

from app.db.models.market_product_listing import MarketProductListing


class PricingService:

    # ==================================================
    # CORE PRICE CALCULATION
    # ==================================================
    def calculate_listing_price(
        self,
        listing: MarketProductListing,
        quantity: int,
        delivery_fee: Decimal = Decimal("0.00")
    ):
        unit_price = listing.unit_price

        subtotal = unit_price * quantity

        market_fee = listing.market_fee * quantity

        platform_fee = (
            subtotal * listing.platform_fee_percent / Decimal("100")
        )

        total = subtotal + market_fee + delivery_fee + platform_fee

        return {
            "unit_price": unit_price,
            "quantity": quantity,
            "subtotal": subtotal,
            "market_fee": market_fee,
            "delivery_fee": delivery_fee,
            "platform_fee": platform_fee,
            "total": total
        }

    # ==================================================
    # COOPERATIVE PRICING (BULK MODE)
    # ==================================================
    def calculate_cooperative_price(
        self,
        listing: MarketProductListing,
        quantity: int,
        members: int
    ):
        base = self.calculate_listing_price(listing, quantity)

        bulk_discount = Decimal("0.00")

        # simple scalable rule (can be expanded later)
        if members >= 50:
            bulk_discount = Decimal("5.00")  # 5%
        elif members >= 20:
            bulk_discount = Decimal("2.00")

        discount_amount = (
            base["subtotal"] * bulk_discount / Decimal("100")
        )

        total = base["total"] - discount_amount

        base["bulk_discount_percent"] = bulk_discount
        base["discount_amount"] = discount_amount
        base["total"] = total

        return base


pricing_service = PricingService()