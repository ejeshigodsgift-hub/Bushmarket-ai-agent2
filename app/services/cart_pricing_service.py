class CartPricingService:

    def calculate_item_total(
        self,
        quantity: int,
        unit_price: float,
        market_fee: float
    ):

        subtotal = quantity * float(unit_price)

        total_fee = quantity * float(market_fee)

        return {
            "subtotal": subtotal,
            "market_fee": total_fee,
            "total": subtotal + total_fee
        }