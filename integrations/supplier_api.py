import requests


class SupplierAPI:

    def place_order(self, product_id, quantity):
        return {
            "status": "confirmed",
            "supplier_order_id": "SUP12345",
            "product_id": product_id,
            "quantity": quantity
        }