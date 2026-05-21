class FinancialCoreClient:

    def hold_escrow(self, cooperative_id: int, amount: float):
        # locks funds
        return True

    def release_payment(self, order_id: int, supplier_id: str, amount: float):
        # releases funds after delivery confirmation
        return True

    def refund(self, user_id: int, amount: float):
        # refund failed/partial procurement
        return True

    def get_coop_balance(self, cooperative_id: int):
        return 0.0