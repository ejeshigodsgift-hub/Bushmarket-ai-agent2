from sqlalchemy.orm import Session
from app.db.models.market_volatility_rule import MarketVolatilityRule


class VolatilityRuleService:

    # =========================
    # GET RULE (SMART FALLBACK)
    # =========================
    def get_rule(self, db: Session, product_id: str, market_id: str):

        # 1. MOST SPECIFIC: product + market
        rule = db.query(MarketVolatilityRule).filter(
            MarketVolatilityRule.product_id == product_id,
            MarketVolatilityRule.market_id == market_id,
            MarketVolatilityRule.is_active == True
        ).first()

        if rule:
            return rule

        # 2. MARKET LEVEL
        rule = db.query(MarketVolatilityRule).filter(
            MarketVolatilityRule.market_id == market_id,
            MarketVolatilityRule.product_id.is_(None),
            MarketVolatilityRule.is_active == True
        ).first()

        if rule:
            return rule

        # 3. GLOBAL DEFAULT
        return db.query(MarketVolatilityRule).filter(
            MarketVolatilityRule.product_id.is_(None),
            MarketVolatilityRule.market_id.is_(None),
            MarketVolatilityRule.is_active == True
        ).first()

    # =========================
    # CLASSIFY VOLATILITY
    # =========================
    def evaluate(self, rule: MarketVolatilityRule, price_change: float):

        if not rule:
            return "unknown"

        adjusted = abs(price_change) * rule.sensitivity_multiplier

        if adjusted >= rule.critical_threshold:
            return "critical"

        if adjusted >= rule.suspicious_threshold:
            return "suspicious"

        return "normal"


volatility_rule_service = VolatilityRuleService()