# app/services/cooperative_extension_service.py

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership

from app.services.cooperative_state_service import (
    cooperative_state_service
)
from app.services.outbox_service import outbox_service


class CooperativeExtensionService:

    async def open_extension_vote(
        self,
        db: AsyncSession,
        cooperative: Cooperative
    ):

        await cooperative_state_service.transition(
            db=db,
            cooperative=cooperative,
            new_state="extension_vote",
            reason="expiry_window_open"
        )

        await outbox_service.queue_event(
            db,
            "cooperative.extension.vote.opened",
            {
                "cooperative_id": cooperative.id
            }
        )

        await db.commit()

        return cooperative

    async def approve_extension(
        self,
        db: AsyncSession,
        cooperative: Cooperative,
        extension_days: int
    ):

        stmt = select(
            CooperativeMembership
        ).where(
            CooperativeMembership.cooperative_id
            == cooperative.id,
            CooperativeMembership.status == "active"
        )

        result = await db.execute(stmt)
        members = result.scalars().all()

        if not members:
            raise ValueError(
                "No active members"
            )

        # Replace with real vote aggregation
        approved = True

        if not approved:
            raise ValueError(
                "Extension vote not approved"
            )

        cooperative.ends_at = (
            cooperative.ends_at
            + timedelta(days=extension_days)
        )

        await cooperative_state_service.transition(
            db=db,
            cooperative=cooperative,
            new_state="active",
            reason="extension_approved"
        )

        await outbox_service.queue_event(
            db,
            "cooperative.extension.approved",
            {
                "cooperative_id": cooperative.id,
                "extension_days": extension_days,
                "new_expiry": cooperative.ends_at.isoformat()
            }
        )

        await db.commit()

        return cooperative

    async def reject_extension(
        self,
        db: AsyncSession,
        cooperative: Cooperative
    ):

        await cooperative_state_service.transition(
            db=db,
            cooperative=cooperative,
            new_state="expired",
            reason="extension_rejected"
        )

        await outbox_service.queue_event(
            db,
            "cooperative.extension.rejected",
            {
                "cooperative_id": cooperative.id
            }
        )

        await db.commit()

        return cooperative


cooperative_extension_service = (
    CooperativeExtensionService()
)