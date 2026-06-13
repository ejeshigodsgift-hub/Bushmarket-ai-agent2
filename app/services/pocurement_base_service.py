class ProcurementBaseService:

    @staticmethod
    def calculate_savings(unit_price, qty, cost):
        retail = unit_price * qty
        savings = retail - cost

        return {
            "retail": retail,
            "savings": savings,
            "percent": (savings / retail) * 100 if retail else 0
        }