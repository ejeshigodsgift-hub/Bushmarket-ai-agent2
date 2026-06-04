

import httpx

from app.integrations.payment_gateway import (PaymentGateway)

from app.core.config import settings

class PaystackGateway(PaymentGateway):

BASE_URL = "https://api.paystack.co"

def __init__(self):

    self.headers = {
        "Authorization":
            f"Bearer {settings.PAYSTACK_SECRET_KEY}",
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
        "amount": int(amount * 100),
        "email": email,
        "reference": reference,
        "metadata": metadata or {}
    }

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{self.BASE_URL}/transaction/initialize",
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
            f"{self.BASE_URL}/transaction/verify/{reference}",
            headers=self.headers
        )

    return response.json()

async def create_transfer_recipient(
    self,
    account_number: str,
    bank_code: str,
    account_name: str
):

    payload = {
        "type": "nuban",
        "name": account_name,
        "account_number": account_number,
        "bank_code": bank_code,
        "currency": "NGN"
    }

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{self.BASE_URL}/transferrecipient",
            json=payload,
            headers=self.headers
        )

    return response.json()

async def initiate_transfer(
    self,
    amount: float,
    recipient_code: str,
    reference: str
):

    payload = {
        "amount": int(amount * 100),
        "recipient": recipient_code,
        "reference": reference
    }

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{self.BASE_URL}/transfer",
            json=payload,
            headers=self.headers
        )

    return response.json()