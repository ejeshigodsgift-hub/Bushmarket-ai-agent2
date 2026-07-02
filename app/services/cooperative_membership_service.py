from datetime import datetime, timezone
from app.integrations.payment_status import PaymentStatus

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership
from app.db.models.platform_settings import PlatformSettings

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from app.services.payment_service import PaymentService

payment_service = PaymentService()


class CooperativeMembershipService:

    def __init__(self):
        self.audit = AuditService()

    # =====================================================
    # JOIN COOPERATIVE (ENFORCED ENTRY GATE)
    # =====================================================
    async def join_cooperative(
        self,
        db: AsyncSession,
        user_id: str,
        cooperative_id: str,
        ip: str | None = None
    ):
        coop = await db.get(Cooperative, cooperative_id)

        if not coop:
            raise HTTPException(404, "Cooperative not found")

        # -----------------------------
        # PLATFORM RULES
        # -----------------------------
        settings = await db.scalar(
            select(PlatformSettings).where(
                PlatformSettings.is_active == True
            )
        )

        if not settings:
            raise HTTPException(500, "Platform settings not configured")

        # -----------------------------
        # MAX MEMBERS ENFORCEMENT
        # -----------------------------
        count = await db.scalar(
            select(func.count(CooperativeMembership.id)).where(
                CooperativeMembership.cooperative_id == cooperative_id,
                CooperativeMembership.status == "active"
            )
        ) or 0

        if count >= settings.max_members:
            raise HTTPException(400, "Cooperative member limit reached")

        # -----------------------------
        # EXISTING MEMBERSHIP CHECK
        # -----------------------------
        stmt = select(CooperativeMembership).where(
            CooperativeMembership.user_id == user_id,
            CooperativeMembership.cooperative_id == cooperative_id
        )

        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            if existing.status in ["active", "pending"]:
                raise HTTPException(409, "Membership already exists")

            membership = existing
        else:
            membership = CooperativeMembership(
                user_id=user_id,
                cooperative_id=cooperative_id,
                status="pending",
                payment_status="pending",
                contribution_amount=coop.contribution_per_member,
                joined_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),

                # tracking fields
                accepted_extension=False,
                accepted_partial_procurement=False,
                accepted_merge=False,
            )
            db.add(membership)

        await db.flush()

        # -----------------------------
        # CREATE PAYMENT INTENT
        # -----------------------------
        payment_intent = await payment_service.create_payment_intent(
            db=db,
            user_id=user_id,
    amount=float(membership.contribution_amount),
            purpose="cooperative_membership",
    reference=f"coop_mem_{membership.id}",
            cooperative_id=cooperative_id,
        )

        membership.payment_reference = payment_intent.id

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="cooperative_join_initiated",
            entity_type="cooperative_membership",
            entity_id=membership.id,
            metadata={
                "cooperative_id": cooperative_id,
                "payment_intent_id": payment_intent.id
            },
            ip=ip
        )

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.membership.pending",
            payload={
                "membership_id": str(membership.id),
                "user_id": user_id,
                "cooperative_id": cooperative_id,
                "payment_intent_id": payment_intent.id
            }
        )

        await db.commit()
        await db.refresh(membership)

        return membership, payment_intent

    # =====================================================
    # ACTIVATE MEMBERSHIP (STRICT PAYMENT GATE)
    # =====================================================
    async def activate_membership(
        self,
        db: AsyncSession,
        membership_id: str,
        payment_reference: str
    ):
        membership = await db.get(CooperativeMembership, membership_id)

        if not membership:
            raise HTTPException(404, "Membership not found")

        if membership.status == "active":
            return membership

        if membership.status != "pending":
            raise HTTPException(409, f"Invalid state: {membership.status}")

        # -----------------------------
        # STRICT PAYMENT ENFORCEMENT
        # -----------------------------
        # Payment already verified by webhook

        if membership.payment_status !=  "paid":
            raise HTTPException(
               402,
                "Payment not completed"
            )

        membership.status = "active"
        membership.payment_status = "paid"
        membership.payment_reference = payment_reference
        membership.activated_at = datetime.now(timezone.utc)

        cooperative = await db.get(
            Cooperative,
            membership.cooperative_id
        )

        if cooperative:
            cooperative.current_members += 1

        await self.audit.log(
            db=db,
            user_id=membership.user_id,
            action="cooperative_membership_activated",
            entity_type="cooperative_membership",
            entity_id=membership.id,
            metadata={"payment_reference": payment_reference}
        )

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.membership.active",
            payload={
                "membership_id": str(membership.id),
                "user_id": membership.user_id,
                "cooperative_id": membership.cooperative_id
            }
        )

        await db.commit()
        return membership

    # =====================================================
    # FAIL MEMBERSHIP
    # =====================================================
    async def fail_membership(self, db, membership_id: str, reason: str = "payment_failed"):
        membership = await db.get(CooperativeMembership, membership_id)

        if not membership:
            raise HTTPException(404, "Membership not found")

        if membership.status == "active":
            raise HTTPException(409, "Cannot fail active membership")

        membership.status = "failed"
        membership.payment_status = "failed"
        membership.failure_reason = reason
        membership.failed_at = datetime.now(timezone.utc)

        await db.commit()
        return membership

    # =====================================================
    # GET STATUS
    # =====================================================
    async def get_membership_status(self, db, user_id: str, cooperative_id: str):
        stmt = select(CooperativeMembership).where(
            CooperativeMembership.user_id == user_id,
            CooperativeMembership.cooperative_id == cooperative_id
        )
        return (await db.execute(stmt)).scalar_one_or_none()