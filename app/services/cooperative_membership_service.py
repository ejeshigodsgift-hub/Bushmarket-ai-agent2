from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service

from app.integrations.financial_core import financial_core


class CooperativeMembershipService:

    def __init__(self):
        self.audit = AuditService()

    # =========================================
    # CREATE MEMBERSHIP (PENDING + PAYMENT INTENT)
    # =========================================
    async def create_pending_membership(
        self,
        db: AsyncSession,
        user_id: str,
        cooperative_id: str,
        ip: str | None = None
    ):
        coop = await db.get(Cooperative,    cooperative_id)

        if not coop:
            raise HTTPException(
                404,
                "Cooperative not found"
           )

    # ----------------------------------
    # ENFORCE MAXIMUM MEMBER LIMIT
    # ----------------------------------
        if coop.current_members >=    coop.max_members:
            raise HTTPException(
                400,
                "Cooperative member limit  reached"
           )

    # -----------------------------
    # CHECK EXISTING MEMBERSHIP
    # -----------------------------
        stmt =   select(CooperativeMembership).where(
           CooperativeMembership.user_id   == user_id,
        CooperativeMembership.cooperative_id == cooperative_id
        )

        existing = (await   db.execute(stmt)).scalar_one_or_none()

        if existing:
            # STRICT STATE HANDLING
            if existing.status in  ["active", "pending"]:
                raise HTTPException(
                    409,
                    "Membership already  exists"
                )

            if existing.status == "failed":
                # allow retry reuse (soft recovery pattern)
                membership = existing
            else:
                membership = existing

        else:
            membership =   CooperativeMembership(
                user_id=user_id,
              cooperative_id=cooperative_id,
                status="pending",
            contribution_amount=coop.contribution_per_member,
            created_at=datetime.now(timezone.utc)
            )
            db.add(membership)

        await db.flush()

        # -----------------------------
        # CREATE PAYMENT INTENT (FINANCIAL CORE)
        # -----------------------------
        payment_intent = await financial_core.create_payment_intent(
            user_id=user_id,
            amount=float(membership.contribution_amount),
            purpose="cooperative_membership",
            reference=f"coop_mem_{membership.id}"
        )

        membership.payment_reference = payment_intent["id"]

        # -----------------------------
        # AUDIT
        # -----------------------------
        await self.audit.log(
            db=db,
            user_id=user_id,
            action="cooperative_join_requested",
            entity_type="cooperative_membership",
            entity_id=membership.id,
            metadata={
                "cooperative_id": cooperative_id,
                "payment_intent_id": payment_intent["id"]
            },
            ip=ip
        )

        # -----------------------------
        # OUTBOX EVENT
        # -----------------------------
        await outbox_service.queue_event(
            db=db,
            topic="cooperative.membership.pending",
            payload={
                "membership_id": str(membership.id),
                "user_id": user_id,
                "cooperative_id": cooperative_id,
                "payment_intent_id": payment_intent["id"]
            }
        )

        await db.commit()
        await db.refresh(membership)

        return membership, payment_intent

    # =========================================
    # ACTIVATE MEMBERSHIP (PAYMENT VERIFIED ONLY)
    # =========================================
    async def activate_membership(
        self,
        db: AsyncSession,
        membership_id: str,
        payment_reference: str
    ):
        membership = await db.get(CooperativeMembership, membership_id)

        if not membership:
            raise HTTPException(404, "Membership not found")

        # -----------------------------
        # IDENTITY / STATE GUARD
        # -----------------------------
        if membership.status == "active":
            return membership

        if membership.status not in ["pending"]:
            raise HTTPException(
                409,
                f"Cannot activate membership in state: {membership.status}"
            )

        # -----------------------------
        # VERIFY PAYMENT WITH FINANCIAL CORE
        # -----------------------------
        payment = await financial_core.verify_payment(payment_reference)

        if not payment or payment["status"] != "success":
            raise HTTPException(402, "Payment not confirmed")

        membership.status = "active"
        membership.payment_reference = payment_reference
        membership.activated_at = datetime.now(timezone.utc)
        membership.failed_at = None
        membership.failure_reason = None

        # -----------------------------
        # AUDIT
        # -----------------------------
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

        # -----------------------------
        # OUTBOX
        # -----------------------------
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
        membership = await db.get(CooperativeMembership, membership_id)

        if not membership:
            raise HTTPException(404, "Membership not found")

        if membership.status == "active":
            raise HTTPException(409, "Cannot fail active membership")

        membership.status = "failed"
        membership.failure_reason = reason
        membership.failed_at = datetime.now(timezone.utc)

        await self.audit.log(
            db=db,
            user_id=membership.user_id,
            action="cooperative_membership_failed",
            entity_type="cooperative_membership",
            entity_id=membership.id,
            metadata={"reason": reason}
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
    # GET STATUS
    # =========================================
    async def get_membership_status(
        self,
        db: AsyncSession,
        user_id: str,
        cooperative_id: str
    ):
        stmt = select(CooperativeMembership).where(
            CooperativeMembership.user_id == user_id,
            CooperativeMembership.cooperative_id == cooperative_id
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()


cooperative_membership_service = CooperativeMembershipService()