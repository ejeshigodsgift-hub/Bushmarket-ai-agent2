from sqlalchemy.orm import Session

from app.db.models.market_product_listing import MarketProductListing
from app.services.listing_validation_service import ListingValidationService
from app.services.audit_service import AuditService
from app.integrations.kafka_client import event_bus
from app.integrations.redis_client import redis_client


class MarketListingService:

    def __init__(self):
        self.validator = ListingValidationService()
        self.audit = AuditService()

    # =========================
    # CREATE LISTING (AGENT ONLY)
    # =========================
    def create_listing(
        self,
        db: Session,
        agent,
        data: dict,
        ip: str
    ):

        # 🔐 AGENT GATE (STRICT)
        if not getattr(agent, "is_verified_agent", False) or agent.status != "approved":
            raise Exception("Agent not authorized")

        # 🧠 VALIDATION GATE
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
            product_id=data["product_id"],
            market_id=data["market_id"],
            measurement_unit_id=data["measurement_unit_id"],
            assigned_agent_id=agent.id,
            unit_price=data["unit_price"],
            available_stock=data["available_stock"],
            status="draft"
        )

        db.add(listing)
        db.commit()
        db.refresh(listing)

        # 📜 AUDIT
        self.audit.log(
            db=db,
            user_id=agent.user_id,
            action="listing_created",
            entity_type="market_listing",
            entity_id=listing.id,
            metadata=data,
            ip=ip
        )

        # 📡 EVENT STREAM
        event_bus.publish("listing.created", {
            "listing_id": listing.id,
            "agent_id": agent.id
        })

        return listing

    # =========================
    # PUBLISH LISTING
    # =========================
    def publish_listing(self, db: Session, listing_id: str):

        listing = db.query(MarketProductListing).filter(
            MarketProductListing.id == listing_id
        ).first()

        if not listing:
            raise Exception("Listing not found")

        listing.status = "active"

        db.commit()

        redis_client.publish("market.listing.active", {
            "listing_id": listing.id,
            "market_id": listing.market_id
        })

        return listing

    # =========================
    # GET LISTINGS
    # =========================
    def get_market_listings(self, db: Session, market_id: str):

        return db.query(MarketProductListing).filter(
            MarketProductListing.market_id == market_id,
            MarketProductListing.status == "active"
        ).all()

    # =========================
    # SEARCH LISTINGS
    # =========================
    def search_market_listings(self, db: Session, keyword: str):

        return db.query(MarketProductListing).filter(
            MarketProductListing.status == "active",
            MarketProductListing.title.ilike(f"%{keyword}%")
        ).all()

    # =========================
    # MARKET FEED
    # =========================
    def get_market_feed(self, db: Session, market_id: str):

        listings = self.get_market_listings(db, market_id)

        return [
            {
                "listing_id": l.id,
                "product_id": l.product_id,
                "price": l.unit_price,
                "stock": l.available_stock,
                "unit": l.measurement_unit_id,
                "agent_id": l.assigned_agent_id
            }
            for l in listings
        ]


market_listing_service = MarketListingService()