from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.db.models.market_product_listing import MarketProductListing
from app.db.models.listing_agent_activity import ListingAgentActivity
from app.services.agent_permission_service import agent_permission_service


class AgentListingService:

    # =========================================
    # CREATE DRAFT LISTING
    # =========================================
    async def create_draft(
        self,
        db: AsyncSession,
        agent_id: str,
        payload: dict,
        ip: str | None = None
    ):

        await agent_permission_service.require_agent(db, agent_id)

        listing = MarketProductListing(
            agent_id=agent_id,
            **payload,
            status="draft"
        )

        db.add(listing)
        await db.flush()

        db.add(ListingAgentActivity(
            listing_id=listing.id,
            agent_id=agent_id,
            action_type="draft_created",
            ip_address=ip,
            is_system_generated=False
        ))

        await db.commit()
        await db.refresh(listing)

        return listing

    # =========================================
    # SUBMIT FOR REVIEW
    # =========================================
    async def submit_for_review(
        self,
        db: AsyncSession,
        agent_id: str,
        listing_id: str
    ):

        await agent_permission_service.require_agent(db, agent_id)

        result = await db.execute(
            select(MarketProductListing).where(
                MarketProductListing.id == listing_id,
                MarketProductListing.agent_id == agent_id
            )
        )

        listing = result.scalar_one_or_none()

        if not listing:
            raise HTTPException(404, "Listing not found")

        if listing.status != "draft":
            raise HTTPException(400, "Only draft listings can be submitted")

        listing.status = "pending_admin_review"

        db.add(ListingAgentActivity(
            listing_id=listing.id,
            agent_id=agent_id,
            action_type="submitted_for_review"
        ))

        await db.commit()
        await db.refresh(listing)

        return listing


    async def update_price(
        self,
        db: AsyncSession,
        agent_id: str,
        listing_id: str,
        new_price: Decimal
        ):

        await   agent_permission_service.require_agent(
            db,
            agent_id
        )

        result = await db.execute(
         select(MarketProductListing).where(
                MarketProductListing.id == listing_id,
                MarketProductListing.agent_id == agent_id
            )
        )

        listing = result.scalar_one_or_none()

        if not listing:
            raise HTTPException(
                404,
                "Listing not found"
            )

        old_price = listing.unit_price

        if old_price == new_price:
            return listing

        listing.unit_price = new_price

        db.add(
            ListingPriceHistory(
                listing_id=listing.id,
                old_price=old_price,
                new_price=new_price,
                updated_by_agent_id=agent_id
            )
        )

        db.add(
            ListingAgentActivity(
                listing_id=listing.id,
                agent_id=agent_id,
                action_type="price_updated"
            )
        )

        await db.commit()
        await db.refresh(listing)

        return listing