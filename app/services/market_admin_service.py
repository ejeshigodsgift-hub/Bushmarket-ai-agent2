from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.market_agent import MarketAgent
from app.db.models.market_product_listing import MarketProductListing

from app.services.audit_service import AuditService
from app.events.outbox_publisher import OutboxPublisher


class MarketAdminService:

    def __init__(self):
        self.audit = AuditService()

    # ====================================================
    # APPROVE AGENT
    # ====================================================
    async def approve_agent(
        self,
        db: AsyncSession,
        user_id: str,
        admin_id: str
    ):

        result = await db.execute(
            select(MarketAgent).where(
                MarketAgent.user_id == user_id
            )
        )

        agent = result.scalar_one_or_none()

        if not agent:
            raise HTTPException(404, "Agent not found")

        agent.status = "approved"
        agent.is_verified_agent = True

        self.audit.log(
            db=db,
            user_id=admin_id,
            action="agent_approved",
            entity_type="market_agent",
            entity_id=agent.id,
            metadata={"user_id": user_id}
        )

        OutboxPublisher.publish(
            db=db,
            event_type="agent.approved",
            payload={
                "user_id": user_id,
                "admin_id": admin_id,
                "agent_id": str(agent.id)
            },
            aggregate_id=agent.id,
            aggregate_type="market_agent"
        )

       # await db.commit()
        await db.refresh(agent)

        return agent

    # ====================================================
    # SUSPEND AGENT
    # ====================================================
    async def suspend_agent(
        self,
        db: AsyncSession,
        user_id: str,
        admin_id: str,
        reason: str = None
    ):

        result = await db.execute(
            select(MarketAgent).where(
                MarketAgent.user_id == user_id
            )
        )

        agent = result.scalar_one_or_none()

        if not agent:
            raise HTTPException(404, "Agent not found")

        agent.status = "suspended"
        agent.is_verified_agent = False

        self.audit.log(
            db=db,
            user_id=admin_id,
            action="agent_suspended",
            entity_type="market_agent",
            entity_id=agent.id,
            metadata={
                "user_id": user_id,
                "reason": reason
            }
        )

        OutboxPublisher.publish(
            db=db,
            event_type="agent.suspended",
            payload={
                "user_id": user_id,
                "admin_id": admin_id,
                "reason": reason
            },
            aggregate_id=agent.id,
            aggregate_type="market_agent"
        )

        await db.commit()
        await db.refresh(agent)

        return agent

    # ====================================================
    # APPROVE LISTING (PUBLISH)
    # ====================================================
    async def approve_listing(
        self,
        db: AsyncSession,
        listing_id: str,
        admin_id: str
    ):

        result = await db.execute(
            select(MarketProductListing).where(
                MarketProductListing.id == listing_id
            )
        )

        listing = result.scalar_one_or_none()

        if not listing:
            raise HTTPException(404, "Listing not found")

        listing.status = "active"

        self.audit.log(
            db=db,
            user_id=admin_id,
            action="listing_approved",
            entity_type="market_listing",
            entity_id=listing.id,
            metadata={"listing_id": listing_id}
        )

        OutboxPublisher.publish(
            db=db,
            event_type="listing.approved",
            payload={
                "listing_id": listing_id,
                "admin_id": admin_id
            },
            aggregate_id=listing.id,
            aggregate_type="market_listing"
        )

        await db.commit()
        await db.refresh(listing)

        return listing

    # ====================================================
    # REJECT LISTING
    # ====================================================
    async def reject_listing(
        self,
        db: AsyncSession,
        listing_id: str,
        admin_id: str,
        reason: str = None
    ):

        result = await db.execute(
            select(MarketProductListing).where(
                MarketProductListing.id == listing_id
            )
        )

        listing = result.scalar_one_or_none()

        if not listing:
            raise HTTPException(404, "Listing not found")

        listing.status = "disabled"

        self.audit.log(
            db=db,
            user_id=admin_id,
            action="listing_rejected",
            entity_type="market_listing",
            entity_id=listing.id,
            metadata={
                "listing_id": listing_id,
                "reason": reason
            }
        )

        OutboxPublisher.publish(
            db=db,
            event_type="listing.rejected",
            payload={
                "listing_id": listing_id,
                "admin_id": admin_id,
                "reason": reason
            },
            aggregate_id=listing.id,
            aggregate_type="market_listing"
        )

        await db.commit()
        await db.refresh(listing)

        return listing