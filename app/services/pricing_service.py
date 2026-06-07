from decimal import Decimal

from app.db.models.pricing_model import PriceBreakdown
from app.db.models.market_product_listing import (
    MarketProductListing
)


class PricingService:

    # ==========================================
    # STANDARD SHOPPING
    # ==========================================
    def calculate_price(
        self,
        listing: MarketProductListing,
        quantity: int,
        delivery_fee: Decimal = Decimal("0.00"),
        tax_percent: Decimal = Decimal("0.00")
    ) -> PriceBreakdown:

        subtotal = listing.unit_price * quantity

        market_fee = listing.market_fee * quantity

        platform_fee = (
            subtotal
            * listing.platform_fee_percent
            / Decimal("100")
        )

        agent_fee = (
            subtotal
            * listing.agent_fee_percent
            / Decimal("100")
        )

        tax_amount = (
            subtotal
            * tax_percent
            / Decimal("100")
        )

        total = (
            subtotal
            + market_fee
            + delivery_fee
            + platform_fee
            + agent_fee
            + tax_amount
        )

        return PriceBreakdown(
            unit_price=listing.unit_price,
            quantity=quantity,
            subtotal=subtotal,
            market_fee=market_fee,
            delivery_fee=delivery_fee,
            platform_fee=platform_fee,
            agent_fee=agent_fee,
            discount_amount=Decimal("0.00"),
            tax_amount=tax_amount,
            total=total
        )

    # ==========================================
    # COOPERATIVE PURCHASE
    # ==========================================
    def calculate_cooperative_price(
        self,
        listing: MarketProductListing,
        quantity: int,
        member_count: int,
        delivery_fee: Decimal = Decimal("0.00")
    ) -> PriceBreakdown:

        result = self.calculate_price(
            listing=listing,
            quantity=quantity,
            delivery_fee=delivery_fee
        )

        discount_percent = Decimal("0")

        if member_count >= 100:
            discount_percent = Decimal("10")

        elif member_count >= 50:
            discount_percent = Decimal("5")

        elif member_count >= 20:
            discount_percent = Decimal("2")

        discount_amount = (
            result.subtotal
            * discount_percent
            / Decimal("100")
        )

        result.discount_amount = discount_amount

        result.total = (
            result.total
            - discount_amount
        )

        return result

    # ==========================================
    # MEMBER CONTRIBUTION
    # ==========================================
    def calculate_member_contribution(
        self,
        total_cost: Decimal,
        members: int
    ) -> Decimal:

        if members <= 0:
            raise ValueError(
                "members must be greater than zero"
            )

        return total_cost / Decimal(str(members))

    # ==========================================
    # AI SHOPPING RESPONSE
    # ==========================================
    def build_ai_response(
        self,
        breakdown: PriceBreakdown
    ):

        return {
            "unit_price": str(breakdown.unit_price),
            "quantity": breakdown.quantity,
            "subtotal": str(breakdown.subtotal),
            "market_fee": str(breakdown.market_fee),
            "delivery_fee": str(breakdown.delivery_fee),
            "platform_fee": str(breakdown.platform_fee),
            "agent_fee": str(breakdown.agent_fee),
            "discount_amount": str(
                breakdown.discount_amount
            ),
            "tax_amount": str(
                breakdown.tax_amount
            ),
            "total": str(breakdown.total)
        }


pricing_service = PricingService()