

import httpx

from app.integrations.payment_gateway import (
PaymentGateway
)

from app.core.config import settings

class FlutterwaveGateway(PaymentGateway):

BASE_URL = "https://api.flutterwave.com/v3"

def __init__(self):

    self.headers = {
        "Authorization":
            f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type":
            "application/json"
    }

async def initialize_payment(
    self,
    amount: float,
    email: str,
    reference: str,
    metadata: dict | None = None
):

    payload = {
        "tx_ref": reference,
        "amount": amount,
        "currency": "NGN",
        "redirect_url":
            settings.PAYMENT_REDIRECT_URL,
        "customer": {
            "email": email
        },
        "meta": metadata or {}
    }

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{self.BASE_URL}/payments",
            json=payload,
            headers=self.headers
        )

    return response.json()

async def verify_payment(
    self,
    reference: str
):

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{self.BASE_URL}/transactions/verify_by_reference?tx_ref={reference}",
            headers=self.headers
        )

    return response.json()

async def create_transfer_recipient(
    self,
    account_number: str,
    bank_code: str,
    account_name: str
):
    return {
        "account_number": account_number,
        "bank_code": bank_code,
        "account_name": account_name
    }

async def initiate_transfer(
    self,
    amount: float,
    recipient_code: str,
    reference: str
):
    raise NotImplementedError()