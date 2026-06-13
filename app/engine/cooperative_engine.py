from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone

from app.services.cooperative_service import cooperative_service
from app.services.cooperative_membership_service import cooperative_membership_service
from app.services.cooperative_payment_service import cooperative_payment_service
from app.services.audit_service import AuditService
from app.integrations.financial_core import financial_core

from app.services.cooperative_state_service import (
    cooperative_state_service
)


class CooperativeEngine:

    def __init__(self):
        self.audit = AuditService()

    # ====================================================
    # JOIN COOPERATIVE
    # ====================================================
    async def join_cooperative(self, db, user_id, cooperative_id, ip=None):

        membership = await cooperative_membership_service.create_pending_membership(
            db=db,
            user_id=user_id,
            cooperative_id=cooperative_id,
            ip=ip
        )

        coop = await cooperative_service.get_cooperative(db, cooperative_id)

        payment_intent = await cooperative_payment_service.initiate_membership_payment(
            db=db,
            membership_id=membership.id,
            user_id=user_id,
            amount=float(coop.contribution_per_member),
            cooperative_id=cooperative_id
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="coop_join_initiated",
            entity_type="cooperative",
            entity_id=cooperative_id,
            metadata={"membership_id": membership.id}
        )

        return {"status": "pending_payment", "payment_intent": payment_intent}

    # ====================================================
    # PAYMENT SUCCESS
    # ====================================================
    async def handle_payment_success(self, db, membership_id, payment_reference, user_id):

        membership = await cooperative_membership_service.activate_membership(
            db=db,
            membership_id=membership_id,
            payment_reference=payment_reference
        )

        coop = await cooperative_service.get_cooperative(db, membership.cooperative_id)

        coop.current_members += 1

        await self._evaluate_cooperative_state(db, coop)

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="coop_payment_success",
            entity_type="cooperative",
            entity_id=coop.id,
            metadata={}
        )

        await db.commit()

        return {"status": "processed", "cooperative_status": coop.status}

    # ====================================================
    # CORE STATE ENGINE (FIXED)
    # ====================================================
    async def _evaluate_cooperative_state(self, db: AsyncSession, coop):

        total_funds = coop.current_members * float(coop.contribution_per_member)

        # FULL FUNDING
        if total_funds >= float(coop.target_amount):

            await CooperativeStateEngine.apply_transition(
                db, coop, "funded", reason="target reached"
            )

            await self.audit.log(
                db=db,
                user_id=coop.creator_id,
                action="coop_funded",
                entity_type="cooperative",
                entity_id=coop.id,
                metadata={"total_funds": total_funds}
            )

        # STILL ACTIVE
        elif coop.current_members < coop.max_members:

            await CooperativeStateEngine.apply_transition(
                db, coop, "active", reason="still recruiting"
            )

        # CAPACITY FULL BUT NOT FUNDED
        else:

            await CooperativeStateEngine.apply_transition(
                db, coop, "active", reason="capacity reached"
            )

    # ====================================================
    # EXPIRY HANDLER
    # ====================================================
    async def handle_expiry(self, db, coop):

        if coop.status in ["funded", "closed"]:
            return coop

        await CooperativeStateEngine.apply_transition(
            db, coop, "expired", reason="lifespan ended"
        )

        await self.audit.log(
            db=db,
            user_id=coop.creator_id,
            action="coop_expired",
            entity_type="cooperative",
            entity_id=coop.id,
            metadata={}
        )

        return await self._evaluate_post_expiry_options(db, coop)

    # ====================================================
    # POST EXPIRY
    # ====================================================
    async def _evaluate_post_expiry_options(self, db, coop):

        if coop.allow_extension:

            coop.expiry_extended_at = datetime.now(timezone.utc) + timedelta(hours=48)

            await CooperativeStateEngine.apply_transition(
                db, coop, "extension_vote"
            )

            return coop

        return await self._trigger_partial_procurement(db, coop)

    # ====================================================
    # PARTIAL PROCUREMENT
    # ====================================================
    async def _trigger_partial_procurement(self, db, coop):

        await CooperativeStateEngine.apply_transition(
            db, coop, "procurement_pending"
        )

        escrow = await financial_core.get_cooperative_escrow(cooperative_id=coop.id)

        available = escrow["available_balance"]

        if available <= 0:

            await CooperativeStateEngine.apply_transition(
                db, coop, "expired"
            )
            return coop

        await financial_core.reserve_for_partial_procurement(
            cooperative_id=coop.id,
            amount=available
        )

        await financial_core.create_partial_order(
            cooperative_id=coop.id,
            amount=available,
            mode="partial"
        )

        return coop

    # ====================================================
    # MANUAL EXTENSION
    # ====================================================
    async def extend_cooperative_48h(self, db, cooperative_id, user_id):

        coop = await cooperative_service.get_cooperative(db, cooperative_id)

        if coop.status != "expired":
            raise HTTPException(400, "Only expired cooperatives can be extended")

        coop.expiry_extended_at = datetime.now(timezone.utc) + timedelta(hours=48)

        await CooperativeStateEngine.apply_transition(
            db, coop, "active", reason="manual extension"
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="coop_48h_extension",
            entity_type="cooperative",
            entity_id=coop.id
        )

        return coop


    async def   sync_payment_from_financial_core(self,   db, payment_reference):

        payment = await   financial_core.verify_payment(payment_ref erence)

        if payment["status"] == "success":
            return await   self.handle_payment_success(
                db=db,
             membership_id=payment["metadata"] ["membership_id"],
            payment_reference=payment_reference,
                user_id=payment["user_id"]
            )

         return await  self.handle_payment_failed(
            db=db,
            membership_id=payment["metadata"]["membership_id"],
            reason="failed"
        )