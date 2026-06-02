from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service


class CooperativeMembershipService:

    def __init__(self):
        self.audit = AuditService()

    # =========================================
    # CREATE PENDING MEMBERSHIP (JOIN REQUEST)
    # =========================================
    async def create_pending_membership(
        self,
        db: AsyncSession,
        user_id: str,
        cooperative_id: str,
        ip: str | None = None
    ):

        coop = await db.get(
            Cooperative,
            cooperative_id
        )

        if not coop:
            raise HTTPException(
                status_code=404,
                detail="Cooperative not found"
            )

        stmt = select(
            CooperativeMembership
        ).where(
            CooperativeMembership.user_id == user_id,
            CooperativeMembership.cooperative_id == cooperative_id
        )

        existing = (
            await db.execute(stmt)
        ).scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Already requested/joined"
            )

        membership = CooperativeMembership(
            user_id=user_id,
            cooperative_id=cooperative_id,
            status="pending",

            # lifecycle timestamps
            created_at=datetime.now(timezone.utc),

            # lifecycle tracking
            activated_at=None,
            failed_at=None,
            failure_reason=None,
            payment_reference=None
        )

        db.add(membership)

        await db.flush()

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="cooperative_join_requested",
            entity_type="cooperative_membership",
            entity_id=membership.id,
            metadata={
                "cooperative_id": cooperative_id
            },
            ip=ip
        )

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.membership.pending",
            payload={
                "membership_id": str(membership.id),
                "user_id": user_id,
                "cooperative_id": cooperative_id
            }
        )

        return membership

    # =========================================
    # ACTIVATE MEMBERSHIP (AFTER PAYMENT)
    # =========================================
    async def activate_membership(
        self,
        db: AsyncSession,
        membership_id: str,
        payment_reference: str
    ):

        membership = await db.get(
            CooperativeMembership,
            membership_id
        )

        if not membership:
            raise HTTPException(
                status_code=404,
                detail="Membership not found"
            )

        membership.status = "active"

        membership.payment_reference = payment_reference

        membership.activated_at = datetime.now(
            timezone.utc
        )

        membership.failed_at = None
        membership.failure_reason = None

        await self.audit.log(
            db=db,
            user_id=membership.user_id,
            action="cooperative_membership_activated",
            entity_type="cooperative_membership",
            entity_id=membership.id,
            metadata={
                "payment_reference": payment_reference
            }
        )

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.membership.active",
            payload={
                "membership_id": str(membership.id),
                "user_id": membership.user_id,
                "cooperative_id": membership.cooperative_id,
                "payment_reference": payment_reference
            }
        )

        await db.commit()

        await db.refresh(membership)

        return membership

    # =========================================
    # FAIL MEMBERSHIP
    # =========================================
    async def fail_membership(
        self,
        db: AsyncSession,
        membership_id: str,
        reason: str = "payment_failed"
    ):

        membership = await db.get(
            CooperativeMembership,
            membership_id
        )

        if not membership:
            raise HTTPException(
                status_code=404,
                detail="Membership not found"
            )

        membership.status = "failed"

        membership.failure_reason = reason

        membership.failed_at = datetime.now(
            timezone.utc
        )

        await self.audit.log(
            db=db,
            user_id=membership.user_id,
            action="cooperative_membership_failed",
            entity_type="cooperative_membership",
            entity_id=membership.id,
            metadata={
                "reason": reason
            }
        )

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.membership.failed",
            payload={
                "membership_id": str(membership.id),
                "user_id": membership.user_id,
                "cooperative_id": membership.cooperative_id,
                "reason": reason
            }
        )

        await db.commit()

        await db.refresh(membership)

        return membership

    # =========================================
    # GET MEMBERSHIP STATUS
    # =========================================
    async def get_membership_status(
        self,
        db: AsyncSession,
        user_id: str,
        cooperative_id: str
    ):

        stmt = select(
            CooperativeMembership
        ).where(
            CooperativeMembership.user_id == user_id,
            CooperativeMembership.cooperative_id == cooperative_id
        )

        result = await db.execute(stmt)

        membership = result.scalar_one_or_none()

        return membership


cooperative_membership_service = CooperativeMembershipService()