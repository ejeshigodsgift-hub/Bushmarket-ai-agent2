# =========================================
# FILE: app/services/withdrawal_service.py
# =========================================

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.wallet import Wallet
from app.db.models.beneficiary import Beneficiary
from app.db.models.withdrawal_request import WithdrawalRequest

from app.services.financial_core_service import (
    financial_core_service
)

from app.services.financial_transaction_service import (
    financial_transaction_service
)

from app.services.fraud_detection_handler import (
    fraud_detection_handler
)


class WithdrawalService:

    async def create_withdrawal(
        self,
        db: AsyncSession,
        user_id: str,
        wallet_id: str,
        beneficiary_id: str,
        amount: Decimal,
        reference: str,
        ip_address: str | None,
        device_id: str | None,
        debit_ledger_account: str,
        credit_ledger_account: str
    ):

        # =====================================
        # BASIC VALIDATION
        # =====================================
        if amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid withdrawal amount"
            )

        # =====================================
        # FRAUD CHECK
        # =====================================
        fraud_result = (
            await fraud_detection_handler.score_transaction(
                db=db,
                user_id=user_id,
                amount=float(amount),
                transaction_type="withdrawal",
                ip_address=ip_address,
                device_id=device_id
            )
        )

        if fraud_result["risk_level"] == "high":
            raise HTTPException(
                status_code=403,
                detail="Withdrawal blocked due to fraud risk"
            )


        if fraud_result["risk_level"] == "medium":
            status = "fraud_review"
        else:
            status = "processing"
     
        # =====================================
        # WALLET VALIDATION
        # =====================================
        wallet = (
            await db.execute(
                select(Wallet)
                .where(
                    Wallet.id == wallet_id
                )
            )
        ).scalar_one_or_none()

        if not wallet:
            raise HTTPException(
                status_code=404,
                detail="Wallet not found"
            )

        if wallet.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Wallet ownership mismatch"
            )

        # =====================================
        # BENEFICIARY VALIDATION
        # =====================================
        beneficiary = (
            await db.execute(
                select(Beneficiary)
                .where(
                    Beneficiary.id == beneficiary_id
                )
            )
        ).scalar_one_or_none()

        if not beneficiary:
            raise HTTPException(
                status_code=404,
                detail="Beneficiary not found"
            )

        if beneficiary.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Beneficiary ownership mismatch"
            )

        # =====================================
        # MONEY MOVEMENT
        # SOURCE OF TRUTH
        # =====================================
        await financial_core_service.wallet_debit(
            db=db,
            wallet_id=wallet_id,
            amount=amount,
            reference=reference,
            debit_ledger_account=debit_ledger_account,
            credit_ledger_account=credit_ledger_account
        )

        # =====================================
        # FINANCIAL TRANSACTION
        # IMMUTABLE RECORD
        # =====================================
        await financial_transaction_service.create_transaction(
            db=db,
            reference=reference,
            transaction_type="withdrawal",
            amount=amount,
            wallet_id=wallet_id,
            debit_ledger_account_id=debit_ledger_account,
            credit_ledger_account_id=credit_ledger_account,
            created_by=user_id,
            metadata={
                "beneficiary_id": beneficiary_id,
                "risk_level": fraud_result["risk_level"],
                "risk_score": fraud_result["risk_score"]
            }
        )

        # =====================================
        # WITHDRAWAL REQUEST
        # =====================================
        withdrawal = WithdrawalRequest(
            wallet_id=wallet_id,
            beneficiary_id=beneficiary_id,
            amount=amount,
            reference=reference,
            status=status
        )

        db.add(withdrawal)

        await db.flush()

        return withdrawal


withdrawal_service = WithdrawalService()