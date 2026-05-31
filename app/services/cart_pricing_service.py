from decimal import Decimal, ROUND_HALF_UP


class CartPricingService:

    def calculate_item_total(
        self,
        quantity: int,
        unit_price: Decimal,
        market_fee: Decimal
    ):
        qty = Decimal(quantity)

        subtotal = (qty * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_fee = (qty * market_fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = (subtotal + total_fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "subtotal": subtotal,
            "market_fee": total_fee,
            "total": total
        }