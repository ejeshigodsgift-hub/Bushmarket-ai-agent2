from dataclasses import dataclass
from typing import Optional, Dict, Any
from decimal import Decimal

# =====================================================
# PAYMENT STATUS STANDARD (SINGLE SOURCE OF TRUTH)
# =====================================================

class PaymentStatus:
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


# =====================================================
# MOCK / REAL FINANCIAL CORE SERVICE
# =====================================================

class FinancialCoreService:

    # =========================================
    # CREATE PAYMENT INTENT
    # =========================================
    async def create_payment_intent(
        self,
        user_id: str,
        amount: float,
        purpose: str,
        reference: str
    ) -> Dict[str, Any]:

        return {
            "id": reference,
            "user_id": user_id,
            "amount": amount,
            "purpose": purpose,
            "status": PaymentStatus.PENDING
        }

    # =========================================
    # VERIFY PAYMENT (STANDARDIZED OUTPUT)
    # =========================================
    async def verify_payment(
        self,
        payment_reference: str
    ) -> Dict[str, Any]:

        """
        This is the SINGLE SOURCE OF TRUTH for payment validation.
        Always returns standardized PaymentStatus values.
        """

        # -------------------------------------------------
        # PLACEHOLDER LOGIC (replace with Paystack/Flutterwave)
        # -------------------------------------------------

        fake_gateway_response = True  # simulate success/failure

        if fake_gateway_response:
            return {
                "status": PaymentStatus.SUCCESS,   # ONLY allowed value
                "reference": payment_reference,
                "amount": None
            }

        return {
            "status": PaymentStatus.FAILED,
            "reference": payment_reference
        }

    # =========================================
    # ESCROW DEPOSIT (USED BY COOPERATIVES)
    # =========================================
    async def escrow_deposit(
        self,
        user_id: str,
        cooperative_id: str,
        amount: Decimal,
        reference: str
    ) -> Dict[str, Any]:

        return {
            "status": PaymentStatus.SUCCESS,
            "user_id": user_id,
            "cooperative_id": cooperative_id,
            "amount": str(amount),
            "reference": reference
        }


# =====================================================
# SINGLETON INSTANCE
# =====================================================

financial_core = FinancialCoreService()