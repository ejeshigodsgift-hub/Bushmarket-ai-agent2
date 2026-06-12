from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_membership import CooperativeMembership

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service
from app.integrations.redis_client import redis_client


class CooperativeService:

    def __init__(self):
        self.audit = AuditService()

    # ====================================================
    # CREATE COOPERATIVE (ASYNC)
    # ====================================================
    async def create_cooperative(
        self,
        db: AsyncSession,
        creator,
        data: dict,
        ip: str | None = None
    ):

        # -----------------------------
        # LOAD PLATFORM SETTINGS
        # -----------------------------
        settings = await db.scalar(
            select(PlatformSettings).where(
                PlatformSettings.is_active == True
            )
        )


        if not settings:
            raise HTTPException(
                500,
                "Platform settings not   configured"
            )

# -----------------------------
# PRODUCT VALIDATION
# -----------------------------
        product_count = len(data["product_ids"])

        if product_count <   settings.min_products:
            raise HTTPException(
                400,
                "At least one target product required"
            )

        if product_count > settings.max_products:
            raise HTTPException(
                400,
                "Maximum target product limit exceeded"
            )

# -----------------------------
# MEMBER VALIDATION
# -----------------------------
        if data["max_members"] <   settings.min_members:
            raise HTTPException(
                400,
                "Minimum member requirement not met"
            )

        if data["max_members"] >   settings.max_members:
            raise HTTPException(
                400,
                "Maximum member limit exceeded"
            )

# -----------------------------
# QUANTITY VALIDATION
# -----------------------------
        if data["target_quantity"] <  settings.min_coop_quantity:
            raise HTTPException(
                400,
                "Target quantity below minimum allowed"
            )

        if data["target_quantity"] > settings.max_coop_quantity:
            raise HTTPException(
                400,
                "Target quantity exceeds maximum allowed"
            )

# -----------------------------
# LIFESPAN VALIDATION
# -----------------------------
        if data["lifespan_days"] <   settings.min_lifespan_days:
            raise HTTPException(
                400,
                "Lifespan below minimum allowed"
            )

        if data["lifespan_days"] >   settings.max_lifespan_days:
            raise HTTPException(
                400,
                "Lifespan exceeds maximum   allowed"
            )

        # -----------------------------
        # BUSINESS RULES
        # -----------------------------
        if data["max_members"] > settings.max_cooperative_members:
            raise HTTPException(
                400,
                "Maximum member limit exceeded"
            )

        if len(data["product_ids"]) > 3:
            raise HTTPException(400, "Max 3 products allowed")

        if data["lifespan_days"] > 60:
            raise HTTPException(400, "Max lifespan exceeded")

        

        # ----------------------------------
# PREVENT DUPLICATE ACTIVE COOPERATIVE
# FOR SAME CREATOR + SAME PRODUCT
# ----------------------------------

        stmt = select(Cooperative).where(
            Cooperative.creator_id == creator.id,
            Cooperative.status.in_(["draft",   "funding", "active"])
        )

        existing_coops = (
            await db.execute(stmt)
        ).scalars().all()

        new_products = set(data["product_ids"])

        for existing in existing_coops:
            existing_products =   set(existing.product_ids or [])

            if  new_products.intersection(existing_products):
                raise HTTPException(
                    400,
                    "You already have an   active cooperative for one or more   selected products"
                )

        # -----------------------------
        # CREATE COOPERATIVE
        # -----------------------------
        coop = Cooperative(
            creator_id=creator.id,
            title=data["title"],
            product_ids=data["product_ids"],
            target_quantity=data["target_quantity"],
            target_amount=data["target_amount"],
            contribution_per_member=data["contribution_per_member"],
            max_members=data["max_members"],
            lifespan_days=data["lifespan_days"],
            status="draft",
            discount_flag=data.get("discount_flag", False),
            market_id=data["market_id"]
        )

        db.add(coop)
        await db.flush()

        # -----------------------------
        # AUDIT
        # -----------------------------
        await self.audit.log(
            db=db,
            user_id=creator.id,
            action="cooperative_created",
            entity_type="cooperative",
            entity_id=coop.id,
            metadata={"coop_id": str(coop.id)},
            ip=ip
        )

        # -----------------------------
        # OUTBOX EVENT
        # -----------------------------
        await outbox_service.queue_event(
            db=db,
            topic="cooperative.created",
            payload={
                "cooperative_id": str(coop.id),
                "creator_id": str(creator.id)
            }
        )

        await db.commit()
        await db.refresh(coop)

        return coop

    # ====================================================
    # GET SINGLE COOPERATIVE
    # ====================================================
    async def get_cooperative(self, db: AsyncSession, coop_id: str):

        result = await db.execute(
            select(Cooperative).where(Cooperative.id == coop_id)
        )

        coop = result.scalar_one_or_none()

        if not coop:
            raise HTTPException(404, "Cooperative not found")

        return coop

    # ====================================================
    # GET ACTIVE COOPERATIVES
    # ====================================================
    async def get_active_cooperatives(self, db: AsyncSession):

        result = await db.execute(
            select(Cooperative).where(
                Cooperative.status.in_(["active", "funding"])
            )
        )

        return result.scalars().all()

    # ====================================================
    # GET USER COOPERATIVES (FIXED MISSING METHOD)
    # ====================================================
    async def get_user_cooperatives(
        self,
        db: AsyncSession,
        user_id: str
    ):

        result = await db.execute(
            select(Cooperative)
            .join(CooperativeMembership)
            .where(CooperativeMembership.user_id == user_id)
        )

        return result.scalars().unique().all()