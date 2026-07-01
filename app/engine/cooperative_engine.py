from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cooperative_service import cooperative_service
from app.services.cooperative_membership_service import (
    cooperative_membership_service,
)
from app.services.cooperative_payment_service import (
    cooperative_payment_service,
)
from app.services.cooperative_state_service import (
    cooperative_state_service,
)
from app.services.audit_service import AuditService

from app.services.financial_core_service import (
    financial_core_service,
)

from app.services.cooperative_partial_procurement_service import (
    cooperative_partial_procurement_service,
)

class CooperativeEngine:

    def __init__(self):
        self.audit = AuditService()

    # ====================================================
    # JOIN COOPERATIVE
    # ====================================================
    async def join_cooperative(
        self,
        db: AsyncSession,
        user_id: str,
        cooperative_id: str,
        ip: str | None = None,
    ):

        membership = (
            await cooperative_membership_service.create_pending_membership(
                db=db,
                user_id=user_id,
                cooperative_id=cooperative_id,
                ip=ip,
            )
        )

        coop = await cooperative_service.get_cooperative(
            db,
            cooperative_id,
        )

        payment_intent = (
            await cooperative_payment_service.initiate_membership_payment(
                db=db,
                membership_id=membership.id,
                user_id=user_id,
                amount=float(coop.contribution_per_member),
                cooperative_id=cooperative_id,
            )
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="coop_join_initiated",
            entity_type="cooperative",
            entity_id=cooperative_id,
            metadata={
                "membership_id": membership.id
            },
        )

        return {
            "status": "pending_payment",
            "payment_intent": payment_intent,
        }

    # ====================================================
    # PAYMENT SUCCESS
    # ====================================================
    async def handle_payment_success(
        self,
        db: AsyncSession,
        membership_id: str,
        payment_reference: str,
        user_id: str,
    ):

        membership = (
            await cooperative_membership_service.activate_membership(
                db=db,
                membership_id=membership_id,
                payment_reference=payment_reference,
            )
        )

        coop = await cooperative_service.get_cooperative(
            db,
            membership.cooperative_id,
        )

        coop.current_members += 1

        await self._evaluate_cooperative_state(
            db,
            coop,
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="coop_payment_success",
            entity_type="cooperative",
            entity_id=coop.id,
            metadata={},
        )

        await db.commit()

        return {
            "status": "processed",
            "cooperative_status": coop.status,
        }

    # ====================================================
    # STATE EVALUATION
    # ====================================================
    async def _evaluate_cooperative_state(
        self,
        db: AsyncSession,
        coop,
    ):

        total_funds = (
            coop.current_members
            * float(coop.contribution_per_member)
        )

        if total_funds >= float(coop.target_amount):

            await cooperative_state_service.transition(
                db=db,
                cooperative=coop,
                new_state="funded",
                reason="target reached",
            )

            await self.audit.log(
                db=db,
                user_id=coop.creator_id,
                action="coop_funded",
                entity_type="cooperative",
                entity_id=coop.id,
                metadata={
                    "total_funds": total_funds
                },
            )

        elif coop.current_members < coop.max_members:

            # Already active → no transition needed
            if coop.status != "active":
                await cooperative_state_service.transition(
                    db=db,
                    cooperative=coop,
                    new_state="active",
                    reason="still recruiting",
                )

        else:

            if coop.status != "active":
                await cooperative_state_service.transition(
                    db=db,
                    cooperative=coop,
                    new_state="active",
                    reason="capacity reached",
                )

    # ====================================================
    # EXPIRY HANDLER
    # ====================================================
    async def handle_expiry(
        self,
        db: AsyncSession,
        coop,
    ):

        if coop.status in ["funded", "closed"]:
            return coop

        await cooperative_state_service.transition(
            db=db,
            cooperative=coop,
            new_state="expired",
            reason="lifespan ended",
        )

        await self.audit.log(
            db=db,
            user_id=coop.creator_id,
            action="coop_expired",
            entity_type="cooperative",
            entity_id=coop.id,
            metadata={},
        )

        return await self._evaluate_post_expiry_options(
            db,
            coop,
        )

    # ====================================================
    # POST EXPIRY
    # ====================================================
    async def _evaluate_post_expiry_options(
        self,
        db: AsyncSession,
        coop,
    ):

        if coop.allow_extension:

            coop.expiry_extended_at = (
                datetime.now(timezone.utc)
                + timedelta(hours=48)
            )

            return coop

        return await self._trigger_partial_procurement(
            db,
            coop,
        )

    # ====================================================
    # PARTIAL PROCUREMENT
    # ====================================================
    async def _trigger_partial_procurement(
        self,
        db: AsyncSession,
        coop,
    ):

        await cooperative_state_service.transition(
            db=db,
            cooperative=coop,
            new_state="procurement_pending",
            reason="partial procurement initiated",
        )

        escrow = await financial_core_service.get_cooperative_escrow(
            db=db,
            cooperative_id=coop.id,
        )

        available = escrow["available_balance"]

        if available <= 0:

            await cooperative_state_service.transition(
                db=db,
                cooperative=coop,
                new_state="refunded",
                reason="no funds available for procurement",
            )

            return coop

        await financial_core_service.reserve_for_partia  l_procurement(
            db=db,
            cooperative_id=coop.id,
            amount=available,
    reference=f"partial-procurement-{coop.id}",
    reserved_ledger_account="PROCUREMENT_RESERVED",
    available_ledger_account="COOPERATIVE_AVAILABLE",
        )

        await cooperative_partial_procurement_service.c reate_partial_order(
            db=db,
            cooperative_id=coop.id,
            listing_id=listing_id,
    requested_quantity=requested_quantity,
        )

        return coop

    # ====================================================
    # MANUAL EXTENSION
    # ====================================================
    async def extend_cooperative_48h(
        self,
        db: AsyncSession,
        cooperative_id: str,
        user_id: str,
    ):

        coop = await cooperative_service.get_cooperative(
            db,
            cooperative_id,
        )

        if coop.status != "expired":
            raise HTTPException(
                400,
                "Only expired cooperatives can be extended",
            )

        coop.expiry_extended_at = (
            datetime.now(timezone.utc)
            + timedelta(hours=48)
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="coop_48h_extension",
            entity_type="cooperative",
            entity_id=coop.id,
        )

        return coop

    # ====================================================
    # PAYMENT SYNC
    # ====================================================
    async def sync_payment_from_financial_core(
        self,
        db: AsyncSession,
        payment_reference: str,
    ):

        payment = await financial_core.verify_payment(
            payment_reference
        )

        if payment["status"] == "success":

            return await self.handle_payment_success(
                db=db,
                membership_id=payment["metadata"]["membership_id"],
                payment_reference=payment_reference,
                user_id=payment["user_id"],
            )

        return await self.handle_payment_failed(
            db=db,
            membership_id=payment["metadata"]["membership_id"],
            reason="failed",
        )