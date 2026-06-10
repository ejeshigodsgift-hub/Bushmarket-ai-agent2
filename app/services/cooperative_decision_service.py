from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative

from app.services.cooperative_state_service import (
    cooperative_state_service
)

from app.services.outbox_service import (
    outbox_service
)


class CooperativeDecisionService:

    async def decide_extend(
        self,
        db: AsyncSession,
        cooperative: Cooperative,
        approved: bool
    ):

        if approved:

            await cooperative_state_service.transition(
                db=db,
                cooperative=cooperative,
                new_state="active",
                reason="extension approved"
            )

            await outbox_service.queue_event(
                db,
                "cooperative.extension.approved",
                {
                    "cooperative_id": cooperative.id
                }
            )

        else:

            await cooperative_state_service.transition(
                db=db,
                cooperative=cooperative,
                new_state="expired",
                reason="extension rejected"
            )

        return cooperative

    async def decide_merge(
        self,
        db: AsyncSession,
        cooperative: Cooperative,
        approved: bool
    ):

        if approved:

            await cooperative_state_service.transition(
                db=db,
                cooperative=cooperative,
                new_state="procurement_pending",
                reason="merge approved"
            )

            await outbox_service.queue_event(
                db,
                "cooperative.merge.approved",
                {
                    "cooperative_id": cooperative.id
                }
            )

        else:

            await cooperative_state_service.transition(
                db=db,
                cooperative=cooperative,
                new_state="active",
                reason="merge rejected"
            )

        return cooperative

    async def decide_partial_procurement(
        self,
        db: AsyncSession,
        cooperative: Cooperative,
        approved: bool
    ):

        if approved:

            await cooperative_state_service.transition(
                db=db,
                cooperative=cooperative,
                new_state="procurement_pending",
                reason="partial procurement approved"
            )

            await outbox_service.queue_event(
                db,
                "cooperative.partial_procurement.approved",
                {
                    "cooperative_id": cooperative.id
                }
            )

        else:

            await cooperative_state_service.transition(
                db=db,
                cooperative=cooperative,
                new_state="active",
                reason="partial procurement rejected"
            )

        return cooperative

    async def decide_full_procurement(
        self,
        db: AsyncSession,
        cooperative: Cooperative
    ):

        await cooperative_state_service.transition(
            db=db,
            cooperative=cooperative,
            new_state="procurement_pending",
            reason="full procurement triggered"
        )

        await outbox_service.queue_event(
            db,
            "cooperative.full_procurement.approved",
            {
                "cooperative_id": cooperative.id
            }
        )

        return cooperative


cooperative_decision_service = CooperativeDecisionService()