from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative
from app.services.outbox_service import outbox_service


class CooperativeFundingService:
    """
    Cooperative Funding Engine

    Responsible for:
    - funding calculations
    - remaining amount calculations
    - remaining member calculations
    - auto funded detection
    - automatic lifecycle transition
    """

    def calculate_funding_percentage(
        self,
        cooperative: Cooperative
    ) -> Decimal:

        if not cooperative.target_amount:
            return Decimal("0")

        percentage = (
            Decimal(str(cooperative.total_contributed))
            / Decimal(str(cooperative.target_amount))
        ) * Decimal("100")

        return min(
            percentage,
            Decimal("100")
        )

    def calculate_remaining_amount(
        self,
        cooperative: Cooperative
    ) -> Decimal:

        remaining = (
            Decimal(str(cooperative.target_amount))
            - Decimal(str(cooperative.total_contributed))
        )

        return max(
            remaining,
            Decimal("0")
        )

    def calculate_remaining_members(
        self,
        cooperative: Cooperative
    ) -> int:

        remaining = (
            cooperative.max_members
            - cooperative.current_members
        )

        return max(
            remaining,
            0
        )

    def is_fully_funded(
        self,
        cooperative: Cooperative
    ) -> bool:

        amount_reached = (
            Decimal(str(cooperative.total_contributed))
            >= Decimal(str(cooperative.target_amount))
        )

        members_reached = (
            cooperative.current_members
            >= cooperative.max_members
        )

        return amount_reached or members_reached

    async def detect_funded_status(
        self,
        db: AsyncSession,
        cooperative: Cooperative
    ) -> bool:

        if not self.is_fully_funded(cooperative):
            return False

        if cooperative.status == "funded":
            return True

        await cooperative_state_service.transition(
            db=db,
            cooperative=cooperative,
            new_state="funded",
            reason="funding target reached"
        )

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.funded",
            payload={
                "cooperative_id": cooperative.id,
                "total_contributed": str(
                    cooperative.total_contributed
                ),
                "current_members": cooperative.current_members
            }
        )

        return True

    async def update_funding_metrics(
        self,
        db: AsyncSession,
        cooperative: Cooperative
    ) -> dict:

        await self.detect_funded_status(
            db,
            cooperative
        )

        return {
            "funding_percentage":
                float(
                    self.calculate_funding_percentage(
                        cooperative
                    )
                ),
            "remaining_amount":
                float(
                    self.calculate_remaining_amount(
                        cooperative
                    )
                ),
            "remaining_members":
                self.calculate_remaining_members(
                    cooperative
                ),
            "is_fully_funded":
                self.is_fully_funded(
                    cooperative
                ),
            "status":
                cooperative.status
        }


cooperative_funding_service = CooperativeFundingService()