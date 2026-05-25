from sqlalchemy.orm import Session

from app.db.models.market_location import MarketLocation
from app.db.models.products import Product
from app.db.models.measurement_unit import MeasurementUnit


class ListingValidationService:

    # =========================
    # VALIDATE CORE REFERENCES
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
            raise ValueError("Invalid price")

        if stock <= 0:
            raise ValueError("Invalid stock")

        if not db.query(Product).filter(Product.id == product_id).first():
            raise ValueError("Invalid product")

        if not db.query(MarketLocation).filter(MarketLocation.id == market_id).first():
            raise ValueError("Invalid market")

        if not db.query(MeasurementUnit).filter(
            MeasurementUnit.id == unit_id
        ).first():
            raise ValueError("Invalid measurement unit")

        return True


listing_validation_service = ListingValidationService()