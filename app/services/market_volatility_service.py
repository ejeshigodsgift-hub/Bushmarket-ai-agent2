# =========================================
# FILE: app/services/volatility_rule_service.py
# =========================================

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_volatility_rule import (
    MarketVolatilityRule
)


class VolatilityRuleService:

    # =========================================
    # GET ACTIVE RULE
    # =========================================
    async def get_rule(
        self,
        db: AsyncSession,
        product_id: str | None,
        market_id: str | None
    ) -> MarketVolatilityRule | None:

        # =========================================
        # PRODUCT + MARKET RULE
        # =========================================
        stmt = (
            select(MarketVolatilityRule)
            .where(
                MarketVolatilityRule.product_id == product_id,
                MarketVolatilityRule.market_id == market_id,
                MarketVolatilityRule.is_active.is_(True)
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        rule = result.scalar_one_or_none()

        if rule:
            return rule

        # =========================================
        # MARKET DEFAULT RULE
        # =========================================
        stmt = (
            select(MarketVolatilityRule)
            .where(
                MarketVolatilityRule.market_id == market_id,
                MarketVolatilityRule.product_id.is_(None),
                MarketVolatilityRule.is_active.is_(True)
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        rule = result.scalar_one_or_none()

        if rule:
            return rule

        # =========================================
        # GLOBAL DEFAULT
        # =========================================
        stmt = (
            select(MarketVolatilityRule)
            .where(
                MarketVolatilityRule.market_id.is_(None),
                MarketVolatilityRule.product_id.is_(None),
                MarketVolatilityRule.is_active.is_(True)
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()

    # =========================================
    # EVALUATE VOLATILITY
    # =========================================
    async def evaluate(
        self,
        rule: MarketVolatilityRule | None,
        percentage_change: float
    ) -> str:

        if not rule:
            return "unknown"

        adjusted_change = abs(
            percentage_change
        ) * float(rule.sensitivity_multiplier)

        if adjusted_change >= float(rule.critical_threshold):
            return "critical"

        if adjusted_change >= float(rule.suspicious_threshold):
            return "suspicious"

        return "normal"


volatility_rule_service = VolatilityRuleService()