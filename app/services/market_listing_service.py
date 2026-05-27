from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models.market_product_listing import MarketProductListing
from app.db.models.inventory import Inventory
from app.db.models.inventory_history import InventoryHistory

from app.services.listing_validation_service import ListingValidationService
from app.services.audit_service import AuditService

from app.integrations.kafka_client import event_bus
from app.integrations.redis_client import redis_client


class MarketListingService:

    def __init__(self):
        self.validator = ListingValidationService()
        self.audit = AuditService()

    # =========================================================
    # CREATE LISTING (AGENT ONLY)
    # =========================================================
    def create_listing(
        self,
        db: Session,
        agent,
        data: dict,
        ip: str
    ):

        # -----------------------------------------------------
        # STRICT VERIFIED AGENT GATE
        # -----------------------------------------------------
        if (
            not getattr(agent, "is_verified_agent", False)
            or getattr(agent, "status", None) != "approved"
        ):
            raise HTTPException(
                status_code=403,
                detail="Agent not authorized"
            )

        # -----------------------------------------------------
        # VALIDATION GATE
        # -----------------------------------------------------
        self.validator.validate_listing_dependencies(
            db=db,
            agent_id=agent.id,
            market_id=data["market_id"],
            product_id=data["product_id"],
            unit_id=data["measurement_unit_id"],
            price=data["unit_price"],
            stock=data["available_stock"]
        )

        # -----------------------------------------------------
        # CREATE LISTING
        # -----------------------------------------------------
        listing = MarketProductListing(
            product_id=data["product_id"],
            market_id=data["market_id"],
            measurement_unit_id=data["measurement_unit_id"],
            assigned_agent_id=agent.id,
            unit_price=data["unit_price"],
            available_stock=data["available_stock"],
            status="draft"
        )

        db.add(listing)
        db.flush()

        # -----------------------------------------------------
        # INVENTORY RECORD
        # -----------------------------------------------------
        inventory = Inventory(
            listing_id=listing.id,
            product_id=data["product_id"],
            market_id=data["market_id"],
            measurement_unit_id=data["measurement_unit_id"],
            quantity_available=data["available_stock"],
            reserved_quantity=0,
            status="available",
            last_restocked_at=datetime.utcnow()
        )

        db.add(inventory)
        db.flush()

        # -----------------------------------------------------
        # INVENTORY HISTORY
        # -----------------------------------------------------
        history = InventoryHistory(
            inventory_id=inventory.id,
            action="inventory_created",
            quantity=data["available_stock"],
            performed_by=agent.user_id,
            metadata={
                "listing_id": listing.id,
                "market_id": data["market_id"]
            }
        )

        db.add(history)

        db.commit()
        db.refresh(listing)

        # -----------------------------------------------------
        # AUDIT LOG
        # -----------------------------------------------------
        self.audit.log(
            db=db,
            user_id=agent.user_id,
            action="listing_created",
            entity_type="market_listing",
            entity_id=listing.id,
            metadata={
                "product_id": data["product_id"],
                "market_id": data["market_id"],
                "stock": data["available_stock"]
            },
            ip=ip
        )

        # -----------------------------------------------------
        # REDIS CACHE
        # -----------------------------------------------------
        redis_client.set(
            f"listing:{listing.id}",
            {
                "listing_id": listing.id,
                "market_id": listing.market_id,
                "product_id": listing.product_id,
                "price": float(listing.unit_price),
                "stock": listing.available_stock,
                "status": listing.status
            },
            ttl=3600
        )

        # -----------------------------------------------------
        # KAFKA EVENT
        # -----------------------------------------------------
        event_bus.publish(
            "listing.created",
            {
                "listing_id": listing.id,
                "agent_id": agent.id,
                "market_id": listing.market_id
            }
        )

        return listing

    # =========================================================
    # PUBLISH LISTING
    # =========================================================
    def publish_listing(
        self,
        db: Session,
        listing_id: str,
        admin_user,
        ip: str
    ):

        listing = db.query(MarketProductListing).filter(
            MarketProductListing.id == listing_id
        ).first()

        if not listing:
            raise HTTPException(
                status_code=404,
                detail="Listing not found"
            )

        if listing.available_stock <= 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot publish empty inventory listing"
            )

        listing.status = "active"

        db.commit()
        db.refresh(listing)

        # CACHE UPDATE
        redis_client.set(
            f"listing:{listing.id}",
            {
                "listing_id": listing.id,
                "status": listing.status,
                "stock": listing.available_stock
            },
            ttl=3600
        )

        # REDIS PUBSUB
        redis_client.publish(
            "market.listing.active",
            {
                "listing_id": listing.id,
                "market_id": listing.market_id
            }
        )

        # AUDIT
        self.audit.log(
            db=db,
            user_id=admin_user.id,
            action="listing_published",
            entity_type="market_listing",
            entity_id=listing.id,
            metadata={
                "market_id": listing.market_id
            },
            ip=ip
        )

        # KAFKA EVENT
        event_bus.publish(
            "listing.published",
            {
                "listing_id": listing.id,
                "market_id": listing.market_id
            }
        )

        return listing

    # =========================================================
    # UPDATE INVENTORY
    # =========================================================
    def update_inventory(
        self,
        db: Session,
        listing_id: str,
        quantity: int,
        actor,
        ip: str
    ):

        listing = db.query(MarketProductListing).filter(
            MarketProductListing.id == listing_id
        ).first()

        if not listing:
            raise HTTPException(
                status_code=404,
                detail="Listing not found"
            )

        inventory = db.query(Inventory).filter(
            Inventory.listing_id == listing.id
        ).first()

        if not inventory:
            raise HTTPException(
                status_code=404,
                detail="Inventory not found"
            )

        new_quantity = inventory.quantity_available + quantity

        if new_quantity < 0:
            raise HTTPException(
                status_code=400,
                detail="Insufficient inventory"
            )

        inventory.quantity_available = new_quantity
        inventory.last_restocked_at = datetime.utcnow()

        listing.available_stock = new_quantity

        if new_quantity <= 0:
            inventory.status = "out_of_stock"
            listing.status = "disabled"

        db.flush()

        # INVENTORY HISTORY
        history = InventoryHistory(
            inventory_id=inventory.id,
            action="inventory_updated",
            quantity=quantity,
            performed_by=actor.id,
            metadata={
                "listing_id": listing.id,
                "new_stock": new_quantity
            }
        )

        db.add(history)

        db.commit()

        # CACHE UPDATE
        redis_client.set(
            f"listing:{listing.id}",
            {
                "listing_id": listing.id,
                "stock": listing.available_stock,
                "status": listing.status
            },
            ttl=3600
        )

        # AUDIT
        self.audit.log(
            db=db,
            user_id=actor.id,
            action="inventory_updated",
            entity_type="inventory",
            entity_id=inventory.id,
            metadata={
                "listing_id": listing.id,
                "new_stock": new_quantity
            },
            ip=ip
        )

        # KAFKA EVENT
        event_bus.publish(
            "inventory.updated",
            {
                "listing_id": listing.id,
                "inventory_id": inventory.id,
                "stock": new_quantity
            }
        )

        return inventory

    # =========================================================
    # GET ACTIVE MARKET LISTINGS
    # =========================================================
    def get_market_listings(
        self,
        db: Session,
        market_id: str
    ):

        return db.query(MarketProductListing).filter(
            MarketProductListing.market_id == market_id,
            MarketProductListing.status == "active",
            MarketProductListing.available_stock > 0
        ).all()

    # =========================================================
    # SEARCH MARKET LISTINGS
    # =========================================================
    def search_market_listings(
        self,
        db: Session,
        keyword: str
    ):

        return db.query(MarketProductListing).filter(
            MarketProductListing.status == "active",
            MarketProductListing.available_stock > 0,
            or_(
                MarketProductListing.title.ilike(f"%{keyword}%"),
                MarketProductListing.description.ilike(f"%{keyword}%")
            )
        ).all()

    # =========================================================
    # MARKET FEED
    # =========================================================
    def get_market_feed(
        self,
        db: Session,
        market_id: str
    ):

        listings = self.get_market_listings(
            db=db,
            market_id=market_id
        )

        return [
            {
                "listing_id": listing.id,
                "product_id": listing.product_id,
                "market_id": listing.market_id,
                "measurement_unit_id": listing.measurement_unit_id,
                "unit_price": float(listing.unit_price),
                "available_stock": listing.available_stock,
                "assigned_agent_id": listing.assigned_agent_id,
                "status": listing.status
            }
            for listing in listings
        ]


market_listing_service = MarketListingService()