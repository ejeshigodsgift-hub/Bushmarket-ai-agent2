from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from decimal import Decimal

from app.db.models.listing_price_history import (
    ListingPriceHistory
)

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
        
        async with db.begin():

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

        async with db.begin():

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

        
        await db.refresh(listing)

        return listing


  


 

    # =========================================
# UPDATE PRICE
# =========================================

    async def update_price(
        self,
        db: AsyncSession,
        agent_id: str,
        listing_id: str,
        new_price: Decimal
    ):

        await agent_permission_service.require_agent(
            db,
            agent_id
        )

        async with db.begin():

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

            if listing.status not in [
                "draft",
                "pending_admin_review"
            ]:
                raise HTTPException(
                    400,
                    "Price cannot be changed   after approval"
                )

            old_price = listing.unit_price

            if new_price <= 0:
                raise HTTPException(
                400,
                    "Invalid price"
                )

            if old_price == new_price:
                return listing

            volatility_result = await market_pricing_service.evaluate_price_change(
                db=db,
            product_id=listing.product_id,
                market_id=listing.market_id,
                old_price=old_price,
                new_price=new_price
            )


            if volatility_result["status"] == "critical":

    # Send listing back for admin review
                listing.status =     "pending_admin_review"

            
                await db.refresh(listing)

                    raise HTTPException(
                        400,
                    "Price change exceeds    allowed volatility threshold"
                )

        


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
                ListingVolatilityLog(
                    listing_id=listing.id,
            volatility_score=volatility_result["percentage_change"],
                    recorded_price=new_price
                )
            )

            db.add(
                ListingAgentActivity(
                    listing_id=listing.id,
                    agent_id=agent_id,
                   action_type="price_updated"
                )
            )

        
        await db.refresh(listing)

        return listing