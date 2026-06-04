from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.wallet import Wallet
from app.db.models.beneficiary import Beneficiary
from app.db.models.withdrawal_request import WithdrawalRequest

from app.integrations.paystack_gateway import PaystackGateway

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from app.services.idempotency_service import idempotency_service


class PayoutService:

    def __init__(self):
        self.gateway = PaystackGateway()
        self.audit = AuditService()

    async def create_withdrawal(
        self,
        db: AsyncSession,
        wallet_id: str,
        beneficiary_id: str,
        amount: Decimal
    ):
        """
        Create withdrawal request
        """

        if amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid amount"
            )

        wallet_stmt = (
            select(Wallet)
            .where(Wallet.id == wallet_id)
            .with_for_update()
        )

        wallet = (
            await db.execute(wallet_stmt)
        ).scalar_one_or_none()

        if not wallet:
            raise HTTPException(
                status_code=404,
                detail="Wallet not found"
            )

        if wallet.balance < amount:
            raise HTTPException(
                status_code=400,
                detail="Insufficient balance"
            )

        beneficiary_stmt = (
            select(Beneficiary)
            .where(Beneficiary.id == beneficiary_id)
        )

        beneficiary = (
            await db.execute(
                beneficiary_stmt
            )
        ).scalar_one_or_none()

        if not beneficiary:
            raise HTTPException(
                status_code=404,
                detail="Beneficiary not found"
            )

        reference = (
            f"WDR-{uuid4().hex.upper()}"
        )

        wallet.balance -= amount
        wallet.version += 1

        withdrawal = WithdrawalRequest(
            wallet_id=wallet.id,
            beneficiary_id=beneficiary.id,
            amount=amount,
            reference=reference,
            status="pending"
        )

        db.add(withdrawal)

        await self.audit.log(
            db=db,
            user_id=wallet.user_id,
            action="withdrawal_created",
            entity_type="withdrawal",
            entity_id=withdrawal.id,
            reference=reference,
            amount=float(amount)
        )

        await outbox_service.queue_event(
            db=db,
            topic="withdrawal.created",
            payload={
                "withdrawal_id": withdrawal.id,
                "wallet_id": wallet.id,
                "amount": str(amount),
                "reference": reference
            }
        )

        await db.flush()

        return withdrawal

    async def process_withdrawal(
        self,
        db: AsyncSession,
        withdrawal_id: str
    ):
        """
        Send money to bank
        """

        stmt = select(
            WithdrawalRequest
        ).where(
            WithdrawalRequest.id == withdrawal_id
        )

        withdrawal = (
            await db.execute(stmt)
        ).scalar_one_or_none()

        if not withdrawal:
            raise HTTPException(
                status_code=404,
                detail="Withdrawal not found"
            )

        beneficiary = withdrawal.beneficiary

        response = (
            await self.gateway.initiate_transfer(
                amount=withdrawal.amount,
                recipient_code=beneficiary.recipient_code,
                reference=withdrawal.reference
            )
        )

        data = response.get(
            "data",
            {}
        )

        withdrawal.status = "processing"

        withdrawal.gateway_reference = (
            data.get("transfer_code")
        )

        await outbox_service.queue_event(
            db=db,
            topic="withdrawal.processing",
            payload={
                "withdrawal_id":
                    withdrawal.id,
                "reference":
                    withdrawal.reference
            }
        )

        return withdrawal

    async def mark_paid(
        self,
        db: AsyncSession,
        withdrawal: WithdrawalRequest
    ):
        withdrawal.status = "paid"

        await outbox_service.queue_event(
            db=db,
            topic="withdrawal.paid",
            payload={
                "withdrawal_id":
                    withdrawal.id,
                "reference":
                    withdrawal.reference
            }
        )

    async def mark_failed(
        self,
        db: AsyncSession,
        withdrawal: WithdrawalRequest,
        reason: str
    ):
        wallet = withdrawal.wallet

        wallet.balance += withdrawal.amount
        wallet.version += 1

        withdrawal.status = "failed"
        withdrawal.failure_reason = reason

        await outbox_service.queue_event(
            db=db,
            topic="withdrawal.failed",
            payload={
                "withdrawal_id":
                    withdrawal.id,
                "reference":
                    withdrawal.reference,
                "reason":
                    reason
            }
        )