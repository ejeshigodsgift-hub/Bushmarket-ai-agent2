from decimal import Decimal

from abc import ABC, abstractmethod

class PaymentGateway(ABC):

@abstractmethod
async def initialize_payment(
    self,
    amount: Decimal,
    email: str,
    reference: str,
    metadata: dict | None = None
):
    pass

@abstractmethod
async def verify_payment(
    self,
    reference: str
):
    pass

@abstractmethod
async def create_transfer_recipient(
    self,
    account_number: str,
    bank_code: str,
    account_name: str
):
    pass

@abstractmethod
async def initiate_transfer(
    self,
    amount: Decimal,
    recipient_code: str,
    reference: str
):
    pass