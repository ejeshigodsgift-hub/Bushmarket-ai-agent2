from decimal import Decimal
from dataclasses import dataclass
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.delivery_fee_rule import DeliveryFeeRule


@dataclass
class DeliveryFeeResult:
    base_fee: Decimal
    distance_fee: Decimal
    total_fee: Decimal


class DeliveryFeeService:

    # ======================================================
    # LOAD ACTIVE RULES
    # ======================================================
    def _get_active_rules(self, db: Session) -> List[DeliveryFeeRule]:
        stmt = select(DeliveryFeeRule).where(
            DeliveryFeeRule.is_active.is_(True)
        )
        return db.execute(stmt).scalars().all()

    # ======================================================
    # CALCULATE SINGLE RULE VALUE
    # ======================================================
    def _calculate_value(
        self,
        distance_km: Decimal,
        rule: DeliveryFeeRule
    ) -> Decimal:

        if rule.is_percentage:
            return distance_km * (Decimal(str(rule.fee_amount)) / Decimal("100"))

        return Decimal(str(rule.fee_amount))

    # ======================================================
    # DELIVERY CALCULATION (SOFT-CODED)
    # ======================================================
    def calculate_delivery_fee(
        self,
        db: Session,
        distance_km: float,
        market_id: Optional[str] = None
    ) -> DeliveryFeeResult:

        distance = Decimal(str(distance_km))

        rules = self._get_active_rules(db)

        base_fee = Decimal("0")
        distance_fee = Decimal("0")

        for rule in rules:

            # FUTURE EXTENSION: market-specific rules
            # if rule.market_id and rule.market_id != market_id:
            #     continue

            value = self._calculate_value(distance, rule)

            if "base" in rule.name.lower():
                base_fee += value

            elif "distance" in rule.name.lower():
                distance_fee += value

        total = base_fee + distance_fee

        return DeliveryFeeResult(
            base_fee=base_fee,
            distance_fee=distance_fee,
            total_fee=total
        )


delivery_fee_service = DeliveryFeeService()