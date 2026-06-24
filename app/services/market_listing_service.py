from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import or_

from app.db.models.market_product_listing import MarketProductListing
from app.db.models.inventory import Inventory
from app.db.models.inventory_history import InventoryHistory
from app.services.listing_admin_activity_service import (
    listing_admin_activity_service
)

from app.db.models.listing_agent_activity import ListingAgentActivity

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.listing_validation_service import ListingValidationService
from app.services.audit_service import AuditService
from app.services.agent_permission_service import agent_permission_service

from app.events.outbox_publisher import OutboxPublisher

from app.db.models.product import Product
from app.services.product_visibility_service import product_visibility_service


class MarketListingService:

    def __init__(self):
        self.validator = ListingValidationService()
        self.audit = AuditService()

    # ====================================================
    # CREATE LISTING
    # ====================================================

    async def create_listing(
        self,
        db: AsyncSession,
        agent,
        data: dict,
        ip: str
    ):

        # ====================================================
        # OPTION 1: CENTRALIZED AGENT APPROVAL CHECK
        # user_id = permission identity
        # agent.id = business actor identity
        # ====================================================
        await agent_permission_service.require_agent(db, agent.user_id)

        # ====================================================
        # VALIDATION
        # ====================================================
        self.validator.validate_listing_dependencies(
            db=db,
            agent_id=agent.id,
            market_id=data["market_id"],
            product_id=data["product_id"],
            unit_id=data["measurement_unit_id"],
            price=data["unit_price"],
            stock=data["available_stock"]
        )

        # ====================================================
        # LISTING CREATION
        # ====================================================
        listing = MarketProductListing(
            market_id=data["market_id"],
            product_id=data["product_id"],
            variant_id=data.get("variant_id"),
            measurement_unit_id=data["measurement_unit_id"],
            assigned_agent_id=agent.id,
            title=data["title"],
            description=data.get("description"),
            unit_price=data["unit_price"],
            market_fee=data.get("market_fee", 0),
            available_stock=data["available_stock"],
            reserved_stock=0,
            sold_stock=0,
            status="draft"
        )

        await db.add(listing)
        await db.flush()

        # ====================================================
        # INVENTORY INIT
        # ====================================================
        inventory = Inventory(
            listing_id=listing.id,
            available_stock=data["available_stock"],
            reserved_stock=0,
            sold_stock=0,
            last_restocked_at=datetime.utcnow()
        )

        await db.add(inventory)
        await db.flush()

        # ====================================================
        # INVENTORY HISTORY
        # ====================================================

        history = InventoryHistory(
            inventory_id=inventory.id,

            previous_available_stock=0,
    new_available_stock=data["available_stock"],

            previous_reserved_stock=0,
            new_reserved_stock=0,

            previous_sold_stock=0,
            new_sold_stock=0,

           change_reason="inventory_created",

            changed_by=agent.user_id
        )

        db.add(history)

        # ====================================================
        # ACTIVITY LOG
        # ====================================================
        activity = ListingAgentActivity(
            listing_id=listing.id,
            agent_id=agent.id,
            action_type="listing_created",
            activity_note="Listing created",
            ip_address=ip
        )

        db.add(activity)

        # ====================================================
        # AUDIT LOG
        # ====================================================
        await self.audit.log(
            db=db,
            user_id=agent.id,
            action="listing_created",
            entity_type="market_listing",
            entity_id=listing.id,
            metadata={"listing_id": str(listing.id)},
            ip=ip
        )

        # ====================================================
        # OUTBOX EVENT
        # ====================================================
        await OutboxPublisher.publish(
            db=db,
            event_type="listing.created",
            payload={
                "listing_id": str(listing.id),
                "market_id": str(listing.market_id),
                "agent_id": str(agent.id)
            },
            aggregate_id=listing.id,
            aggregate_type="market_listing"
        )

        await db.commit()
        await db.refresh(listing)

        return listing

    # ====================================================
    # PUBLISH LISTING
    # ====================================================

    
    async def publish_listing(
        self,
        db: AsyncSession,
        listing_id,
        admin_user,
        ip: str
    ):

        result = await db.execute(
            select(MarketProductListing).where(
                MarketProductListing.id == listing_id
            )
        )

        listing = result.scalar_one_or_none()

        if not listing:
            raise HTTPException(404, "Listing not found")

        if listing.available_stock <= 0:
            raise HTTPException(400, "No stock available")

        listing.status = "active"

        await listing_admin_activity_service.log_listing_published(
            db=db,
            listing_id=listing.id,
            admin_id=admin_user.id,
            ip=ip
        )

        await self.audit.log(
            db=db,
            user_id=admin_user.id,
            action="listing_published",
            entity_type="market_listing",
            entity_id=listing.id,
            ip=ip
        )

        await OutboxPublisher.publish(
            db=db,
            event_type="listing.published",
            payload={
                "listing_id": str(listing.id),
                "market_id": str(listing.market_id)
            },
            aggregate_id=listing.id,
            aggregate_type="market_listing"
        )

        await db.commit()
        await db.refresh(listing)

        return listing
    # ====================================================
    # UPDATE INVENTORY
    # ====================================================
      

    async def update_inventory(
        self,
        db: AsyncSession,
        listing_id,
        quantity: int,
        actor,
        ip: str
    ):

        result = await db.execute(
            select(MarketProductListing).where(
                MarketProductListing.id == listing_id
            )
        )
        listing = result.scalar_one_or_none()

        if not listing:
            raise HTTPException(404, "Listing not found")

        result = await db.execute(
            select(Inventory).where(
                Inventory.listing_id == listing.id
            )
        )
        inventory = result.scalar_one_or_none()

        if not inventory:
            raise HTTPException(404, "Inventory not found")

        old_stock = inventory.available_stock
        new_stock = old_stock + quantity

        if new_stock < 0:
            raise HTTPException(400, "Insufficient stock")

        inventory.available_stock = new_stock
        inventory.last_restocked_at = datetime.utcnow()
        listing.available_stock = new_stock

        if new_stock <= 0:
            listing.status = "sold_out"

        history = InventoryHistory(
            inventory_id=inventory.id,
            previous_available_stock=old_stock,
            new_available_stock=new_stock,
            previous_reserved_stock=inventory.reserved_stock,
            new_reserved_stock=inventory.reserved_stock,
            previous_sold_stock=inventory.sold_stock,
            new_sold_stock=inventory.sold_stock,
            change_reason=f"inventory_adjustment:{quantity}",
            changed_by=actor.id
        )

        db.add(history)

        await listing_admin_activity_service.log_inventory_updated(
            db=db,
            listing_id=listing.id,
            admin_id=actor.id,
            quantity=quantity,
            ip=ip
        )

        await self.audit.log(
            db=db,
            user_id=actor.id,
            action="inventory_updated",
            entity_type="inventory",
            entity_id=inventory.id,
            metadata={"new_stock": new_stock},
            ip=ip
        )

        await OutboxPublisher.publish(
            db=db,
            event_type="inventory.updated",
            payload={
                "listing_id": str(listing.id),
                "inventory_id": str(inventory.id),
                "available_stock": new_stock
            },
            aggregate_id=inventory.id,
            aggregate_type="inventory"
        )

        await db.commit()
        await db.refresh(inventory)

        return inventory

    # ====================================================
    # GET ACTIVE LISTINGS
    # ====================================================

    async def get_market_listings(
        self,
        db: AsyncSession,
        market_id
    ):
        stmt = select(MarketProductListing).where(
            MarketProductListing.market_id == market_id,
            MarketProductListing.status == "active",
        MarketProductListing.available_stock > 0,
        MarketProductListing.is_active.is_(True)
        )

        result = await db.execute(stmt)

        return result.scalars().all()

    # ====================================================
    # SEARCH LISTINGS
    # ====================================================

    async def search_market_listings(
        self,
        db: AsyncSession,
        keyword: str
    ):
        stmt = select(MarketProductListing).where(
            MarketProductListing.status == "active",
        MarketProductListing.is_active.is_(True),
            or_(
            MarketProductListing.title.ilike(f"%{keyword}%"),
            MarketProductListing.description.ilike(f"%{keyword}%")
            )
        )

        result = await db.execute(stmt)

        return result.scalars().all()
    # ====================================================
    # MARKET FEED
    # ====================================================

    
    async def get_market_feed(
        self,
        db: AsyncSession,
        market_id
    ):
        stmt = (
            select(MarketProductListing)
            .options(
            selectinload(MarketProductListing.product)
            )
            .where(
            MarketProductListing.market_id == market_id,
                MarketProductListing.status == "active",
            MarketProductListing.available_stock > 0,
            MarketProductListing.is_active.is_(True)
            )
        )

        result = await db.execute(stmt)

        listings = result.scalars().all()

        response = []

        for x in listings:

            product = None

            if x.product:
                product = product_visibility_service.apply_visibility(
                    x.product
                )

            response.append({
                "listing_id": str(x.id),
                "title": x.title,
                "product_id": str(x.product_id),
                "product": {
                    "image_url": product.image_url if product else None,
                    "image_status": product.image_status if product else None
                },
                "market_id": str(x.market_id),

                # Decimal value preserved
                "unit_price": x.unit_price
                if isinstance(x.unit_price, Decimal)
                else Decimal(str(x.unit_price)),

                "available_stock": x.available_stock,
                "status": x.status
            })

        return response


    # ====================================================
# GET SINGLE LISTING
# ====================================================
    async def get_listing(
        self,
        db: AsyncSession,
        listing_id: str
    ):
        result = await db.execute(
        select(MarketProductListing).where(
                MarketProductListing.id == listing_id
            )
        )

        return result.scalar_one_or_none()


market_listing_service = MarketListingService()


