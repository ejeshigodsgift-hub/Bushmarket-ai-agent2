import requests


class PaystackClient:

    def charge(self, email, amount, reference):
        return {
            "status": "success",
            "reference": reference
        }


class StripeClient:

    def charge(self, email, amount, reference):
        return {
            "status": "success",
            "reference": reference
        }