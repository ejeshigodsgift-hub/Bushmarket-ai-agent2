from sqlalchemy.orm import Session

from app.db.models.market_listing import MarketListing

from app.services.listing_validation_service import ListingValidationService
from app.services.audit_service import AuditService

from app.integrations.kafka_client import event_bus
from app.integrations.redis_client import redis_client


class MarketListingService:

    def __init__(self):

        self.validator = ListingValidationService()
        self.audit = AuditService()

    # =========================
    # CREATE LISTING (AGENT ONLY - SAFE VERSION)
    # =========================
    def create_listing(
        self,
        db: Session,
        agent,
        data: dict,
        ip: str
    ):

        # 🔐 AGENT GATE
        if not agent.is_verified_agent or agent.status != "approved":
            raise Exception("Agent not authorized")

        listing = MarketListing(
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

        # 🔐 AUDIT LOG
        self.audit.log(
            db=db,
            user_id=agent.user_id,
            action="listing_created",
            entity_type="market_listing",
            entity_id=listing.id,
            metadata=data,
            ip=ip
        )

        # 📡 EVENT BUS (Kafka)
        event_bus.publish("listing.created", {
            "listing_id": listing.id,
            "agent_id": agent.id
        })

        return listing

    # =========================
    # PUBLISH LISTING (ADMIN / AGENT APPROVED FLOW)
    # =========================
    def publish_listing(self, db: Session, listing_id: str):

        listing = db.query(MarketListing).filter(
            MarketListing.id == listing_id
        ).first()

        # 🧠 FULL VALIDATION GATE
        self.validator.validate_listing(listing)

        listing.status = "active"

        db.commit()

        # ⚡ REALTIME MARKET UPDATE
        redis_client.publish("market.listing.active", {
            "listing_id": listing.id,
            "market_id": listing.market_id
        })

        return listing

    # =========================
    # GET MARKET LISTINGS (APP + AI + LIVE MARKET)
    # =========================
    def get_market_listings(
        self,
        db: Session,
        market_id: str
    ):

        return db.query(MarketListing).filter(
            MarketListing.market_id == market_id,
            MarketListing.status == "active"
        ).all()

    # =========================
    # SEARCH MARKET LISTINGS (AI SEARCH ENGINE)
    # =========================
    def search_market_listings(
        self,
        db: Session,
        keyword: str
    ):

        return db.query(MarketListing).filter(
            MarketListing.status == "active",
            MarketListing.product_id.ilike(f"%{keyword}%")
        ).all()

    # =========================
    # MARKET FEED (AI + LIVE MARKET VIEW)
    # =========================
    def get_market_feed(
        self,
        db: Session,
        market_id: str
    ):

        listings = db.query(MarketListing).filter(
            MarketListing.market_id == market_id,
            MarketListing.status == "active"
        ).all()

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