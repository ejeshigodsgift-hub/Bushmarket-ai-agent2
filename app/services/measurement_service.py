from sqlalchemy.orm import Session

from app.db.models.measurement_unit import MeasurementUnit
from app.db.models.product_measurement import ProductMeasurement


class MeasurementService:

    # =========================
    # CREATE UNIT
    # =========================
    def create_measurement_unit(
        self,
        db: Session,
        data: dict
    ):

        unit = MeasurementUnit(**data)

        db.add(unit)
        db.commit()
        db.refresh(unit)

        return unit

    # =========================
    # ASSIGN UNIT TO PRODUCT
    # =========================
    def assign_product_measurement(
        self,
        db: Session,
        data: dict
    ):

        mapping = ProductMeasurement(**data)

        db.add(mapping)
        db.commit()
        db.refresh(mapping)

        return mapping

    # =========================
    # GET PRODUCT MEASUREMENTS
    # =========================
    def get_product_measurements(
        self,
        db: Session,
        product_id: str
    ):

        return db.query(ProductMeasurement).filter(
            ProductMeasurement.product_id == product_id,
            ProductMeasurement.is_active == True
        ).all()


measurement_service = MeasurementService()