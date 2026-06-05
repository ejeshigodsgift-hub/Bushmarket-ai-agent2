from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.payment_transaction import PaymentTransaction
from app.db.models.audit_log import AuditLog
from app.db.models.wallet import Wallet


class FraudDetectionHandler:

    HIGH_RISK_SCORE = 80
    MEDIUM_RISK_SCORE = 50

    async def score_transaction(
        self,
        db: AsyncSession,
        user_id: str,
        amount: float,
        ip_address: str | None = None,
        device_id: str | None = None
    ):

        score = 0
        reasons = []

        # ==================================
        # HIGH AMOUNT CHECK
        # ==================================

        if amount >= 500000:
            score += 30
            reasons.append("high_amount")

        # ==================================
        # VELOCITY CHECK
        # ==================================

        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        tx_count = await db.execute(
            select(func.count())
            .select_from(PaymentTransaction)
            .where(
                PaymentTransaction.created_at >= one_hour_ago
            )
        )

        tx_count = tx_count.scalar() or 0

        if tx_count >= 10:
            score += 25
            reasons.append("high_velocity")

        # ==================================
        # FAILED PAYMENT CHECK
        # ==================================

        failed = await db.execute(
            select(func.count())
            .select_from(PaymentTransaction)
            .where(
                PaymentTransaction.status == "failed"
            )
        )

        failed = failed.scalar() or 0

        if failed >= 5:
            score += 15
            reasons.append("multiple_failures")

        # ==================================
        # DEVICE CHECK
        # ==================================

        if not device_id:
            score += 10
            reasons.append("missing_device")

        # ==================================
        # IP CHECK
        # ==================================

        if not ip_address:
            score += 10
            reasons.append("missing_ip")

        return {
            "risk_score": score,
            "risk_level": self._risk_level(score),
            "reasons": reasons
        }

    def _risk_level(self, score):

        if score >= self.HIGH_RISK_SCORE:
            return "high"

        if score >= self.MEDIUM_RISK_SCORE:
            return "medium"

        return "low"