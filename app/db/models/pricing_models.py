from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PriceBreakdown:

    unit_price: Decimal
    quantity: int

    subtotal: Decimal

    market_fee: Decimal
    delivery_fee: Decimal
    platform_fee: Decimal
    agent_fee: Decimal

    discount_amount: Decimal
    tax_amount: Decimal

    total: Decimal