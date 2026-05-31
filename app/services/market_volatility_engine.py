# =========================================
# FILE: app/services/market_volatility_engine.py
# =========================================

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_product_price import (
    MarketPrice
)

from app.services.volatility_rule_service import (
    volatility_rule_service
)


class MarketVolatilityEngine:

    # =========================================
    # DETECT MARKET VOLATILITY
    # =========================================
    async def detect_volatility(
        self,
        db: AsyncSession,
        product_id: str,
        market_id: str,
        new_price: Decimal
    ) -> dict:

        # =========================================
        # GET LATEST MARKET PRICE
        # =========================================
        stmt = (
            select(MarketPrice)
            .where(
                MarketPrice.product_id == product_id,
                MarketPrice.market_id == market_id
            )
            .order_by(
                MarketPrice.created_at.desc()
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        latest_price = result.scalar_one_or_none()

        if not latest_price:
            return {
                "status": "normal",
                "percentage_change": 0
            }

        old_price = Decimal(str(latest_price.unit_price))

        if old_price <= 0:
            return {
                "status": "normal",
                "percentage_change": 0
            }

        percentage_change = (
            (new_price - old_price) / old_price
        ) * 100

        # =========================================
        # GET RULE
        # =========================================
        rule = await volatility_rule_service.get_rule(
            db=db,
            product_id=product_id,
            market_id=market_id
        )

        # =========================================
        # EVALUATE
        # =========================================
        status = await volatility_rule_service.evaluate(
            rule=rule,
            percentage_change=float(percentage_change)
        )

        return {
            "status": status,
            "percentage_change": round(
                float(percentage_change),
                2
            ),
            "previous_price": float(old_price),
            "new_price": float(new_price)
        }


market_volatility_engine = MarketVolatilityEngine()