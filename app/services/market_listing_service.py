from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models.market_product_listing import MarketProductListing
from app.db.models.inventory import Inventory
from app.db.models.inventory_history import InventoryHistory
from app.db.models.listing_agent_activity import ListingAgentActivity

from app.services.listing_validation_service import ListingValidationService
from app.services.audit_service import AuditService

from app.services.agent_permission_service import agent_permission_service

from app.events.outbox_publisher import OutboxPublisher


class MarketListingService:

    def __init__(self):
        self.validator = ListingValidationService()
        self.audit = AuditService()

    # ====================================================
    # CREATE LISTING
    # ====================================================

    async def create_listing(
        self,
        db: Session,
        agent,
        data: dict,
        ip: str
    ):

        # ====================================================
        # CENTRALIZED AGENT CHECK (NEW RULE)
        # ====================================================
        is_agent = await agent_permission_service.is_agent(
            db,
            agent.user_id
        )

        if not is_agent:
            raise HTTPException(
                status_code=403,
                detail="Agent not authorized"
            )

        self.validator.validate_listing_dependencies(
            db=db,
            agent_id=agent.id,
            market_id=data["market_id"],
            product_id=data["product_id"],
            unit_id=data["measurement_unit_id"],
            price=data["unit_price"],
            stock=data["available_stock"]
        )

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

        db.add(listing)
        db.flush()

        inventory = Inventory(
            listing_id=listing.id,
            available_stock=data["available_stock"],
            reserved_stock=0,
            sold_stock=0,
            last_restocked_at=datetime.utcnow()
        )

        db.add(inventory)
        db.flush()

        history = InventoryHistory(
            inventory_id=inventory.id,
            action="inventory_created",
            quantity=data["available_stock"],
            performed_by=agent.id,
            metadata={
                "listing_id": str(listing.id)
            }
        )

        db.add(history)

        activity = ListingAgentActivity(
            listing_id=listing.id,
            agent_id=agent.id,
            action_type="listing_created",
            activity_note="Listing created",
            ip_address=ip
        )

        db.add(activity)

        self.audit.log(
            db=db,
            user_id=agent.id,
            action="listing_created",
            entity_type="market_listing",
            entity_id=listing.id,
            metadata={"listing_id": str(listing.id)},
            ip=ip
        )

        OutboxPublisher.publish(
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

        db.commit()
        db.refresh(listing)

        return listing

    # ====================================================
    # PUBLISH LISTING
    # ====================================================

    def publish_listing(
        self,
        db: Session,
        listing_id,
        admin_user,
        ip: str
    ):

        listing = db.query(MarketProductListing).filter(
            MarketProductListing.id == listing_id
        ).first()

        if not listing:
            raise HTTPException(404, "Listing not found")

        if listing.available_stock <= 0:
            raise HTTPException(400, "No stock available")

        listing.status = "active"

        activity = ListingAgentActivity(
            listing_id=listing.id,
            agent_id=admin_user.id,
            action_type="listing_published",
            activity_note="Listing published",
            ip_address=ip
        )

        db.add(activity)

        self.audit.log(
            db=db,
            user_id=admin_user.id,
            action="listing_published",
            entity_type="market_listing",
            entity_id=listing.id,
            ip=ip
        )

        OutboxPublisher.publish(
            db=db,
            event_type="listing.published",
            payload={
                "listing_id": str(listing.id),
                "market_id": str(listing.market_id)
            },
            aggregate_id=listing.id,
            aggregate_type="market_listing"
        )

        db.commit()
        db.refresh(listing)

        return listing

    # ====================================================
    # UPDATE INVENTORY
    # ====================================================

    def update_inventory(
        self,
        db: Session,
        listing_id,
        quantity: int,
        actor,
        ip: str
    ):

        listing = db.query(MarketProductListing).filter(
            MarketProductListing.id == listing_id
        ).first()

        if not listing:
            raise HTTPException(404, "Listing not found")

        inventory = db.query(Inventory).filter(
            Inventory.listing_id == listing.id
        ).first()

        if not inventory:
            raise HTTPException(404, "Inventory not found")

        new_stock = inventory.available_stock + quantity

        if new_stock < 0:
            raise HTTPException(400, "Insufficient stock")

        inventory.available_stock = new_stock
        inventory.last_restocked_at = datetime.utcnow()
        listing.available_stock = new_stock

        if new_stock <= 0:
            listing.status = "sold_out"

        history = InventoryHistory(
            inventory_id=inventory.id,
            action="inventory_updated",
            quantity=quantity,
            performed_by=actor.id,
            metadata={"new_stock": new_stock}
        )

        db.add(history)

        activity = ListingAgentActivity(
            listing_id=listing.id,
            agent_id=actor.id,
            action_type="inventory_updated",
            activity_note=f"Inventory adjusted by {quantity}",
            ip_address=ip
        )

        db.add(activity)

        self.audit.log(
            db=db,
            user_id=actor.id,
            action="inventory_updated",
            entity_type="inventory",
            entity_id=inventory.id,
            metadata={"new_stock": new_stock},
            ip=ip
        )

        OutboxPublisher.publish(
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

        db.commit()
        db.refresh(inventory)

        return inventory

    # ====================================================
    # GET ACTIVE LISTINGS
    # ====================================================

    def get_market_listings(self, db: Session, market_id):
        return db.query(MarketProductListing).filter(
            MarketProductListing.market_id == market_id,
            MarketProductListing.status == "active",
            MarketProductListing.available_stock > 0,
            MarketProductListing.is_active.is_(True)
        ).all()

    # ====================================================
    # SEARCH LISTINGS
    # ====================================================

    def search_market_listings(self, db: Session, keyword: str):
        return db.query(MarketProductListing).filter(
            MarketProductListing.status == "active",
            MarketProductListing.is_active.is_(True),
            or_(
                MarketProductListing.title.ilike(f"%{keyword}%"),
                MarketProductListing.description.ilike(f"%{keyword}%")
            )
        ).all()

    # ====================================================
    # MARKET FEED
    # ====================================================

    def get_market_feed(self, db: Session, market_id):

        listings = self.get_market_listings(db, market_id)

        return [
            {
                "listing_id": str(x.id),
                "title": x.title,
                "product_id": str(x.product_id),
                "market_id": str(x.market_id),
                "unit_price": float(x.unit_price),
                "available_stock": x.available_stock,
                "status": x.status
            }
            for x in listings
        ]


market_listing_service = MarketListingService()