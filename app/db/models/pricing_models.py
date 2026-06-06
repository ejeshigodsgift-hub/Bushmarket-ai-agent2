from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PriceBreakdown:
    unit_price: Decimal
    quantity: int

    market_fee: Decimal
    delivery_fee: Decimal
    platform_fee: Decimal

    subtotal: Decimal
    total: Decimal