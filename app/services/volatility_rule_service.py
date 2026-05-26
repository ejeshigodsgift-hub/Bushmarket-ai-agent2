from sqlalchemy.orm import Session

from app.db.models.market_volatility_rule import MarketVolatilityRule


class VolatilityRuleService:

    # =========================
    # GET RULE (SMART FALLBACK CHAIN)
    # =========================
    def get_rule(
        self,
        db: Session,
        product_id: str,
        market_id: str
    ) -> MarketVolatilityRule | None:

        # 1. PRODUCT + MARKET (MOST SPECIFIC)
        rule = db.query(MarketVolatilityRule).filter(
            MarketVolatilityRule.product_id == product_id,
            MarketVolatilityRule.market_id == market_id,
            MarketVolatilityRule.is_active == True
        ).first()

        if rule:
            return rule

        # 2. MARKET LEVEL RULE
        rule = db.query(MarketVolatilityRule).filter(
            MarketVolatilityRule.market_id == market_id,
            MarketVolatilityRule.product_id.is_(None),
            MarketVolatilityRule.is_active == True
        ).first()

        if rule:
            return rule

        # 3. GLOBAL SYSTEM DEFAULT
        return db.query(MarketVolatilityRule).filter(
            MarketVolatilityRule.market_id.is_(None),
            MarketVolatilityRule.product_id.is_(None),
            MarketVolatilityRule.is_active == True
        ).first()

    # =========================
    # CLASSIFY PRICE VOLATILITY
    # =========================
    def evaluate(
        self,
        rule: MarketVolatilityRule,
        price_change: float
    ) -> str:

        if not rule:
            return "unknown"

        # 🧠 apply market sensitivity multiplier (core Bushmarket logic)
        adjusted_change = abs(price_change) * float(rule.sensitivity_multiplier or 1)

        if adjusted_change >= rule.critical_threshold:
            return "critical"

        if adjusted_change >= rule.suspicious_threshold:
            return "suspicious"

        return "normal"


volatility_rule_service = VolatilityRuleService()