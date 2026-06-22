from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.payment_transaction import PaymentTransaction
from app.db.models.financial_transaction import FinancialTransaction


class FraudDetectionHandler:

    # ==================================
    # BASE THRESHOLDS (GLOBAL)
    # ==================================
    HIGH_RISK_SCORE = 80
    MEDIUM_RISK_SCORE = 50
    HIGH_RISK_AMOUNT = 500_000

    # ==================================
    # TRANSACTION TYPE MULTIPLIERS
    # ==================================
    RISK_MULTIPLIERS = {
        "withdrawal": 1.5,
        "escrow_release": 1.3,
        "transfer": 1.0,
        "deposit": 0.7
    }

    # ==================================
    # TRANSACTION TYPE THRESHOLDS
    # ==================================
    THRESHOLDS = {
        "withdrawal": {"high": 70, "medium": 40},
        "escrow_release": {"high": 75, "medium": 45},
        "transfer": {"high": 85, "medium": 60},
        "deposit": {"high": 90, "medium": 70}
    }

    # ==================================
    # MAIN SCORING ENGINE
    # ==================================
    async def score_transaction(
        self,
        db: AsyncSession,
        user_id: str,
        amount: float,
        transaction_type: str,
        ip_address: str | None = None,
        device_id: str | None = None
    ):
        base_score = 0
        reasons = []

        # ==================================
        # HIGH AMOUNT CHECK
        # ==================================
        if amount >= self.HIGH_RISK_AMOUNT:
            base_score += 30
            reasons.append("high_amount")

        # ==================================
        # VELOCITY CHECK (FINANCIAL CORE ONLY)
        # ==================================
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        tx_count_result = await db.execute(
            select(func.count())
            .select_from(FinancialTransaction)
            .where(
                FinancialTransaction.created_at >= one_hour_ago,
                FinancialTransaction.shopper_id == user_id
            )
        )

        tx_count = tx_count_result.scalar() or 0

        if tx_count >= 10:
            base_score += 25
            reasons.append("high_velocity")

        # ==================================
        # FAILED PAYMENT SIGNAL (NOT TRUTH)
        # ==================================
        failed_result = await db.execute(
            select(func.count())
            .select_from(PaymentTransaction)
            .where(
                PaymentTransaction.status == "failed",
                PaymentTransaction.created_at >= one_hour_ago
            )
        )

        failed = failed_result.scalar() or 0

        if failed >= 5:
            base_score += 15
            reasons.append("multiple_failures")

        # ==================================
        # DEVICE CHECK
        # ==================================
        if not device_id:
            base_score += 10
            reasons.append("missing_device")

        # ==================================
        # IP CHECK
        # ==================================
        if not ip_address:
            base_score += 10
            reasons.append("missing_ip")

        # ==================================
        # APPLY TRANSACTION TYPE MULTIPLIER
        # ==================================
        multiplier = self.RISK_MULTIPLIERS.get(transaction_type, 1.0)
        final_score = base_score * multiplier

        # ==================================
        # GET THRESHOLDS FOR TYPE
        # ==================================
        thresholds = self.THRESHOLDS.get(
            transaction_type,
            {"high": 80, "medium": 50}
        )

        return {
            "base_score": base_score,
            "multiplier": multiplier,
            "final_score": final_score,
            "risk_level": self._risk_level(final_score, thresholds),
            "reasons": reasons
        }

    # ==================================
    # TYPE-AWARE RISK CLASSIFICATION
    # ==================================
    def _risk_level(self, score: float, thresholds: dict) -> str:

        if score >= thresholds["high"]:
            return "high"

        if score >= thresholds["medium"]:
            return "medium"

        return "low"