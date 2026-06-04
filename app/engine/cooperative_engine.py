# =========================================
# FILE: app/engines/cooperative_engine.py
# =========================================

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone

from app.services.cooperative_service import cooperative_service
from app.services.cooperative_membership_service import cooperative_membership_service
from app.services.cooperative_payment_service import cooperative_payment_service
from app.services.audit_service import AuditService
from app.integrations.financial_core import financial_core


class CooperativeEngine:
    """
    FULL COOPERATIVE STATE ENGINE

    Handles:
    - Funding lifecycle
    - Partial procurement
    - Expiry + extension
    - Escrow-safe financial transitions
    - Ledger-consistent operations
    """

    def __init__(self):
        self.audit = AuditService()

    # ====================================================
    # 1. JOIN COOPERATIVE
    # ====================================================
    async def join_cooperative(
        self,
        db: AsyncSession,
        user_id: str,
        cooperative_id: str,
        ip: str | None = None
    ):
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
    # 2. PAYMENT SUCCESS → STATE TRANSITION ENGINE
    # ====================================================
    async def handle_payment_success(
        self,
        db: AsyncSession,
        membership_id: str,
        payment_reference: str,
        user_id: str
    ):
        membership = await cooperative_membership_service.activate_membership(
            db=db,
            membership_id=membership_id,
            payment_reference=payment_reference
        )

        coop = await cooperative_service.get_cooperative(
            db,
            membership.cooperative_id
        )

        coop.current_members += 1

        # STATE ENGINE ENTRY POINT
        await self._evaluate_cooperative_state(db, coop)

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="coop_payment_success",
            entity_type="cooperative",
            entity_id=coop.id,
            metadata={
                "membership_id": membership_id,
                "payment_reference": payment_reference
            }
        )

        await db.commit()

        return {
            "status": "processed",
            "cooperative_status": coop.status
        }

    # ====================================================
    # 3. PAYMENT FAILURE
    # ====================================================
    async def handle_payment_failed(
        self,
        db: AsyncSession,
        membership_id: str,
        reason: str = "payment_failed"
    ):
        membership = await cooperative_membership_service.fail_membership(
            db=db,
            membership_id=membership_id,
            reason=reason
        )

        await self.audit.log(
            db=db,
            user_id=membership.user_id,
            action="coop_payment_failed",
            entity_type="cooperative",
            entity_id=membership.cooperative_id,
            metadata={"reason": reason}
        )

        await db.commit()

        return {"status": "failed"}

    # ====================================================
    # 4. STATE ENGINE CORE (THE HEART OF SYSTEM)
    # ====================================================
    async def _evaluate_cooperative_state(self, db: AsyncSession, coop):
        """
        FULL STATE MACHINE LOGIC
        """

        total_funds = coop.current_members * float(coop.contribution_per_member)

        # ==========================
        # FULL FUNDING ACHIEVED
        # ==========================
        if total_funds >= float(coop.target_amount):
            coop.status = "funded"

            await self.audit.log(
                db=db,
                user_id=coop.creator_id,
                action="coop_funded",
                entity_type="cooperative",
                entity_id=coop.id,
                metadata={"total_funds": total_funds}
            )

        # ==========================
        # STILL ACTIVE FUNDING
        # ==========================
        elif coop.current_members < coop.max_members:
            coop.status = "active"

        # ==========================
        # CAPACITY REACHED BUT NOT FUNDED
        # ==========================
        else:
            coop.status = "funding"

    # ====================================================
    # 5. EXPIRY HANDLER (TRIGGERS STATE CHANGE)
    # ====================================================
    async def handle_expiry(self, db: AsyncSession, coop):
        """
        Called by scheduler when lifespan ends
        """

        if coop.status in ["funded", "closed"]:
            return coop

        coop.status = "expired"

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
    # 6. POST-EXPIRY ENGINE (EXTENSION OR PARTIAL PROCUREMENT)
    # ====================================================
    async def _evaluate_post_expiry_options(self, db: AsyncSession, coop):
        """
        Decide what happens after expiry
        """

        total_funds = coop.current_members * float(coop.contribution_per_member)

        # ==========================
        # OPTION A: EXTENSION (48H)
        # ==========================
        if coop.allow_extension:
            coop.status = "extension_granted"
            coop.expiry_extended_at = datetime.now(timezone.utc) + timedelta(hours=48)

            await self.audit.log(
                db=db,
                user_id=coop.creator_id,
                action="coop_extension_granted",
                entity_type="cooperative",
                entity_id=coop.id
            )

            return coop

        # ==========================
        # OPTION B: PARTIAL PROCUREMENT
        # ==========================
        return await self._trigger_partial_procurement(db, coop)

    # ====================================================
    # 7. PARTIAL PROCUREMENT ENGINE
    # ====================================================
    async def _trigger_partial_procurement(self, db: AsyncSession, coop):
        """
        Escrow-safe partial execution
        """

        coop.status = "partial_procurement"

        escrow = await financial_core.get_cooperative_escrow(
            cooperative_id=coop.id
        )

        available_funds = escrow["available_balance"]

        if available_funds <= 0:
            coop.status = "failed"
            return coop

        # Lock funds in FinancialCore (CRITICAL)
        await financial_core.reserve_for_partial_procurement(
            cooperative_id=coop.id,
            amount=available_funds
        )

        await financial_core.create_partial_order(
            cooperative_id=coop.id,
            amount=available_funds,
            mode="partial"
        )

        await self.audit.log(
            db=db,
            user_id=coop.creator_id,
            action="coop_partial_procurement_started",
            entity_type="cooperative",
            entity_id=coop.id,
            metadata={"amount": available_funds}
        )

        return coop

    # ====================================================
    # 8. MANUAL EXTENSION (48H SURVIVAL MODE)
    # ====================================================
    async def extend_cooperative_48h(
        self,
        db: AsyncSession,
        cooperative_id: str,
        user_id: str
    ):
        coop = await cooperative_service.get_cooperative(db, cooperative_id)

        if coop.status != "expired":
            raise HTTPException(400, "Only expired cooperatives can be extended")

        coop.expiry_extended_at = datetime.now(timezone.utc) + timedelta(hours=48)
        coop.status = "active"

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="coop_48h_extension",
            entity_type="cooperative",
            entity_id=coop.id
        )

        return coop

    # ====================================================
    # 9. EXTERNAL FINANCIAL SYNC (TRUTH RECONCILIATION)
    # ====================================================
    async def sync_payment_from_financial_core(
        self,
        db: AsyncSession,
        payment_reference: str
    ):
        payment = await financial_core.verify_payment(payment_reference)

        if payment["status"] == "success":
            return await self.handle_payment_success(
                db=db,
                membership_id=payment["metadata"]["membership_id"],
                payment_reference=payment_reference,
                user_id=payment["user_id"]
            )

        return await self.handle_payment_failed(
            db=db,
            membership_id=payment["metadata"]["membership_id"],
            reason="failed"
        )


# SINGLETON
cooperative_engine = CooperativeEngine()