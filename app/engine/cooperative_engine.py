# =========================================
# FILE: app/engines/cooperative_engine.py
# =========================================

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.services.cooperative_service import cooperative_service
from app.services.cooperative_membership_service import cooperative_membership_service
from app.services.cooperative_payment_service import cooperative_payment_service
from app.services.audit_service import AuditService
from app.integrations.financial_core import financial_core


class CooperativeEngine:

    def __init__(self):
        self.audit = AuditService()

    # ====================================================
    # 1. JOIN COOPERATIVE (FULL FLOW ENTRY POINT)
    # ====================================================
    async def join_cooperative(
        self,
        db: AsyncSession,
        user_id: str,
        cooperative_id: str,
        ip: str | None = None
    ):
        """
        FULL FLOW:
        join → pending membership → payment → return intent
        """

        # STEP 1: create pending membership
        membership = await cooperative_membership_service.create_pending_membership(
            db=db,
            user_id=user_id,
            cooperative_id=cooperative_id,
            ip=ip
        )

        coop = await cooperative_service.get_cooperative(db, cooperative_id)

        # STEP 2: initiate payment
        payment_intent = await cooperative_payment_service.initiate_membership_payment(
            db=db,
            membership_id=membership.id,
            user_id=user_id,
            amount=float(coop.contribution_per_member),
            cooperative_id=cooperative_id
        )

        # STEP 3: audit engine action
        await self.audit.log(
            db=db,
            user_id=user_id,
            action="cooperative_engine_join_initiated",
            entity_type="cooperative",
            entity_id=cooperative_id,
            metadata={
                "membership_id": membership.id,
                "payment_intent_id": payment_intent["id"]
            },
            ip=ip
        )

        return {
            "membership_id": membership.id,
            "payment_intent": payment_intent,
            "status": "pending_payment"
        }

    # ====================================================
    # 2. PAYMENT SUCCESS (WEBHOOK ENTRY POINT)
    # ====================================================
    async def handle_payment_success(
        self,
        db: AsyncSession,
        membership_id: str,
        payment_reference: str,
        user_id: str
    ):
        """
        WEBHOOK FLOW:
        payment success → activate membership → update coop state
        """

        # STEP 1: activate membership
        membership = await cooperative_membership_service.activate_membership(
            db=db,
            membership_id=membership_id,
            payment_reference=payment_reference
        )

        coop = await cooperative_service.get_cooperative(
            db,
            membership.cooperative_id
        )

        # STEP 2: update cooperative member count
        coop.current_members += 1

        # STEP 3: check funding condition
        await self._check_funding_progress(db, coop)

        # STEP 4: audit
        await self.audit.log(
            db=db,
            user_id=user_id,
            action="cooperative_engine_payment_success",
            entity_type="cooperative",
            entity_id=coop.id,
            metadata={
                "membership_id": membership_id,
                "payment_reference": payment_reference
            }
        )

        await db.commit()

        return {
            "status": "membership_activated",
            "cooperative_status": coop.status
        }

    # ====================================================
    # 3. PAYMENT FAILED (WEBHOOK ENTRY POINT)
    # ====================================================
    async def handle_payment_failed(
        self,
        db: AsyncSession,
        membership_id: str,
        reason: str = "payment_failed"
    ):
        """
        PAYMENT FAILURE FLOW
        """

        membership = await cooperative_membership_service.fail_membership(
            db=db,
            membership_id=membership_id,
            reason=reason
        )

        await self.audit.log(
            db=db,
            user_id=membership.user_id,
            action="cooperative_engine_payment_failed",
            entity_type="cooperative",
            entity_id=membership.cooperative_id,
            metadata={
                "membership_id": membership_id,
                "reason": reason
            }
        )

        await db.commit()

        return {
            "status": "failed",
            "reason": reason
        }

    # ====================================================
    # 4. FUNDING LOGIC (CORE BUSINESS ENGINE)
    # ====================================================
    async def _check_funding_progress(
        self,
        db: AsyncSession,
        coop
    ):
        """
        Determines if cooperative is funded
        """

        total_funds = coop.current_members * float(coop.contribution_per_member)

        if total_funds >= float(coop.target_amount):

            coop.status = "funded"

            await self.audit.log(
                db=db,
                user_id=coop.creator_id,
                action="cooperative_funded",
                entity_type="cooperative",
                entity_id=coop.id,
                metadata={
                    "total_funds": total_funds
                }
            )

        elif coop.current_members >= coop.max_members:

            coop.status = "active"

        else:
            coop.status = "active"

        return coop

    # ====================================================
    # 5. EXTERNAL PAYMENT SYNC (FINANCIAL CORE CALLBACK)
    # ====================================================
    async def sync_payment_from_financial_core(
        self,
        db: AsyncSession,
        payment_reference: str
    ):
        """
        Reconciliation layer (VERY IMPORTANT for real systems)
        """

        payment = await financial_core.verify_payment(payment_reference)

        if payment["status"] == "success":

            return await self.handle_payment_success(
                db=db,
                membership_id=payment["metadata"]["membership_id"],
                payment_reference=payment_reference,
                user_id=payment["user_id"]
            )

        else:

            return await self.handle_payment_failed(
                db=db,
                membership_id=payment["metadata"]["membership_id"],
                reason=payment.get("failure_reason", "failed")
            )


cooperative_engine = CooperativeEngine()