from app.services.volatility_rule_service import volatility_rule_service


class MarketVolatilityEngine:

    # =========================
    # MAIN ENTRY POINT
    # =========================
    def analyze_price_change(
        self,
        db,
        product_id: str,
        market_id: str,
        price_change: float
    ):

        rule = volatility_rule_service.get_rule(
            db,
            product_id,
            market_id
        )

        level = volatility_rule_service.evaluate(rule, price_change)

        return {
            "volatility_level": level,
            "price_change": price_change,
            "rule_id": rule.id if rule else None
        }


market_volatility_engine = MarketVolatilityEngine()