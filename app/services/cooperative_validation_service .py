from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership


class CooperativeValidationService:

    # ====================================================
    # RULES CONFIG (SOFT-CODED HOOK)
    # ====================================================
    async def load_rules(self, db: AsyncSession) -> dict:
        return {
            "max_members": 30,
            "max_lifespan_days": 60,
            "min_contribution": 100,
            "max_contribution": 100000,
            "allow_join_only_active": True,
            "allow_payment_retry": True
        }

    # ====================================================
    # 1. VALIDATE COOPERATIVE CREATION
    # ====================================================
    async def validate_cooperative_creation(
        self,
        db: AsyncSession,
        creator_id: str,
        product_ids: list[str],
        target_amount: Decimal,
        lifespan_days: int,
        max_members: int
    ):

        rules = await self.load_rules(db)

        # USER CHECK
        user = (await db.execute(
            select(User).where(User.id == creator_id)
        )).scalar_one_or_none()

        if not user:
            raise HTTPException(404, "Creator not found")

        # PRODUCT RULES
        if len(product_ids) > 3:
            raise HTTPException(400, "Max 3 products allowed")

        # AMOUNT RULES
        if target_amount < rules["min_contribution"]:
            raise HTTPException(400, "Contribution too low")

        if target_amount > rules["max_contribution"]:
            raise HTTPException(400, "Contribution too high")

        # LIFESPAN RULES
        if lifespan_days > rules["max_lifespan_days"]:
            raise HTTPException(400, "Lifespan exceeded")

        # MEMBER LIMIT
        if max_members > rules["max_members"]:
            raise HTTPException(400, "Too many members")

        return True

    # ====================================================
    # 2. VALIDATE JOIN COOPERATIVE
    # ====================================================
    async def validate_join_cooperative(
        self,
        db: AsyncSession,
        user_id: str,
        cooperative_id: str
    ):

        coop = (await db.execute(
            select(Cooperative).where(Cooperative.id == cooperative_id)
        )).scalar_one_or_none()

        if not coop:
            raise HTTPException(404, "Cooperative not found")

        if not coop.is_active:
            raise HTTPException(400, "Cooperative inactive")

        if coop.status != "active":
            raise HTTPException(400, "Cooperative not open for joining")

        # duplicate check
        existing = (await db.execute(
            select(CooperativeMembership).where(
                CooperativeMembership.user_id == user_id,
                CooperativeMembership.cooperative_id == cooperative_id
            )
        )).scalar_one_or_none()

        if existing:
            raise HTTPException(400, "Already joined cooperative")

        # capacity check
        member_count = (await db.execute(
            select(CooperativeMembership).where(
                CooperativeMembership.cooperative_id == cooperative_id
            )
        )).scalars().all()

        if len(member_count) >= coop.max_members:
            raise HTTPException(400, "Cooperative full")

        return True

    # ====================================================
    # 3. VALIDATE PAYMENT INITIATION (JOIN → PAY FLOW)
    # ====================================================
    async def validate_payment_initiation(
        self,
        db: AsyncSession,
        membership_id: str,
        user_id: str
    ):

        membership = (await db.execute(
            select(CooperativeMembership).where(
                CooperativeMembership.id == membership_id,
                CooperativeMembership.user_id == user_id
            )
        )).scalar_one_or_none()

        if not membership:
            raise HTTPException(404, "Membership not found")

        if membership.status != "pending":
            raise HTTPException(
                400,
                "Payment already processed or invalid state"
            )

        coop = (await db.execute(
            select(Cooperative).where(
                Cooperative.id == membership.cooperative_id
            )
        )).scalar_one_or_none()

        if not coop:
            raise HTTPException(404, "Cooperative not found")

        return membership

    # ====================================================
    # 4. VALIDATE PAYMENT CALLBACK (WEBHOOK ENTRY POINT)
    # ====================================================
    async def validate_payment_webhook(
        self,
        db: AsyncSession,
        payment_reference: str,
        status: str
    ):

        membership = (await db.execute(
            select(CooperativeMembership).where(
                CooperativeMembership.payment_reference == payment_reference
            )
        )).scalar_one_or_none()

        if not membership:
            raise HTTPException(404, "Membership not found for payment")

        if membership.status != "pending":
            raise HTTPException(
                400,
                "Membership already processed"
            )

        if status not in ["success", "failed"]:
            raise HTTPException(400, "Invalid payment status")

        return membership

    # ====================================================
    # 5. VALIDATE ACTIVATION (FINAL STATE CHANGE)
    # ====================================================
    async def validate_activation(
        self,
        db: AsyncSession,
        membership: CooperativeMembership
    ):

        coop = (await db.execute(
            select(Cooperative).where(
                Cooperative.id == membership.cooperative_id
            )
        )).scalar_one_or_none()

        if not coop:
            raise HTTPException(404, "Cooperative not found")

        if coop.status not in ["active", "funding"]:
            raise HTTPException(
                400,
                "Cooperative not accepting activations"
            )

        return True

    # ====================================================
    # 6. VALIDATE FAILED PAYMENT STATE
    # ====================================================
    async def validate_payment_failure(
        self,
        membership: CooperativeMembership
    ):

        if membership.status != "pending":
            raise HTTPException(
                400,
                "Cannot fail non-pending membership"
            )

        return True


# SINGLETON
cooperative_validation_service = CooperativeValidationService()