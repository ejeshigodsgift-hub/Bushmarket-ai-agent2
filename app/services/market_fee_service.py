from decimal import Decimal
from dataclasses import dataclass
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.market_fee_rule import MarketFeeRule


@dataclass
class FeeBreakdown:
    market_fee: Decimal
    platform_fee: Decimal
    agent_fee: Decimal


class MarketFeeService:

    # ======================================================
    # LOAD ACTIVE RULES (SOFT CONFIG)
    # ======================================================
    def _get_active_rules(self, db: Session) -> List[MarketFeeRule]:
        stmt = select(MarketFeeRule).where(
            MarketFeeRule.is_active.is_(True)
        )
        return db.execute(stmt).scalars().all()

    # ======================================================
    # PARSE RULE VALUE
    # ======================================================
    def _calculate_value(self, subtotal: Decimal, rule: MarketFeeRule) -> Decimal:
        if rule.is_percentage:
            return subtotal * (Decimal(str(rule.fee_amount)) / Decimal("100"))
        return Decimal(str(rule.fee_amount))

    # ======================================================
    # MARKET FEE CALCULATION (SOFT-CODED)
    # ======================================================
    def calculate_fees(
        self,
        db: Session,
        subtotal: Decimal,
        market_id: Optional[str] = None
    ) -> FeeBreakdown:

        rules = self._get_active_rules(db)

        market_fee = Decimal("0")
        platform_fee = Decimal("0")
        agent_fee = Decimal("0")

        for rule in rules:

            # OPTIONAL: future multi-market filtering
            # if rule.market_id and rule.market_id != market_id:
            #     continue

            value = self._calculate_value(subtotal, rule)

            name = rule.name.lower()

            if "market" in name:
                market_fee += value

            elif "platform" in name:
                platform_fee += value

            elif "agent" in name:
                agent_fee += value

        return FeeBreakdown(
            market_fee=market_fee,
            platform_fee=platform_fee,
            agent_fee=agent_fee
        )


market_fee_service = MarketFeeService()