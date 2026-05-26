from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models.market_location import MarketLocation
from app.db.models.products import Product
from app.db.models.measurement_unit import MeasurementUnit
from app.db.models.market_listing import MarketListing


class ListingValidationService:

    # =========================
    # 1. PRE-CREATION VALIDATION (STRICT DB GATE)
    # =========================
    def validate_listing_dependencies(
        self,
        db: Session,
        agent_id: str,
        market_id: str,
        product_id: str,
        unit_id: str,
        price: float,
        stock: int
    ):

        if price <= 0:
            raise HTTPException(400, "Invalid price")

        if stock <= 0:
            raise HTTPException(400, "Invalid stock")

        if not db.query(Product).filter(Product.id == product_id).first():
            raise HTTPException(404, "Invalid product")

        if not db.query(MarketLocation).filter(MarketLocation.id == market_id).first():
            raise HTTPException(404, "Invalid market")

        if not db.query(MeasurementUnit).filter(
            MeasurementUnit.id == unit_id
        ).first():
            raise HTTPException(404, "Invalid measurement unit")

        return True

    # =========================
    # 2. RUNTIME LISTING VALIDATION (MARKET SAFE GATE)
    # =========================
    def validate_listing(self, listing: MarketListing):

        if not listing:
            raise HTTPException(404, "Listing not found")

        if listing.status != "active":
            raise HTTPException(400, "Listing is not active")

        # 🧩 AGENT GATE
        if not listing.assigned_agent_id:
            raise HTTPException(400, "No agent assigned")

        if not listing.agent:
            raise HTTPException(400, "Agent missing")

        if not listing.agent.is_verified_agent:
            raise HTTPException(403, "Agent not verified")

        if listing.agent.status != "approved":
            raise HTTPException(403, "Agent not approved")

        # 🧩 MARKET SAFETY
        if not listing.market_id:
            raise HTTPException(400, "Invalid market location")

        # 🧩 PRODUCT SAFETY
        if not listing.product_id:
            raise HTTPException(400, "Invalid product")

        # 🧩 UNIT SAFETY
        if not listing.measurement_unit_id:
            raise HTTPException(400, "Invalid measurement unit")

        # 🧩 PRICE SAFETY
        if listing.unit_price is None or listing.unit_price <= 0:
            raise HTTPException(400, "Invalid price")

        # 🧩 STOCK SAFETY
        if listing.available_stock is None or listing.available_stock <= 0:
            raise HTTPException(400, "Out of stock")

        return True


listing_validation_service = ListingValidationService()