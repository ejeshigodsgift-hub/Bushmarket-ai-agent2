# =========================================
# FILE: app/services/market_pricing_service.py
# =========================================

from decimal import Decimal

from app.services.volatility_rule_service import (
    volatility_rule_service
)


class MarketPricingService:

    """
    Dynamic pricing engine.

    Handles:
    - Market volatility
    - Agent pricing safety
    - Anti-manipulation logic
    - Production-safe decimal pricing
    """

    async def evaluate_price_change(
        self,
        db,
        product_id: str,
        market_id: str,
        old_price: Decimal,
        new_price: Decimal
    ) -> dict:

        if old_price <= 0:
            return {
                "status": "invalid",
                "percentage_change": Decimal("0")
            }

        change_percentage = (
            (new_price - old_price) / old_price
        )

        rule = await volatility_rule_service.get_rule(
            db=db,
            product_id=product_id,
            market_id=market_id
        )

        level = volatility_rule_service.evaluate(
            rule=rule,
            price_change=float(change_percentage)
        )

        return {
            "status": level,
            "percentage_change": change_percentage
        }


market_pricing_service = MarketPricingService()