from sqlalchemy.orm import Session

from app.db.models.measurement_conversion import MeasurementConversion


class ConversionService:

    def convert(
        self,
        db: Session,
        from_unit_id: str,
        to_unit_id: str,
        value: float
    ):

        conversion = db.query(
            MeasurementConversion
        ).filter(
            MeasurementConversion.from_measurement_unit_id == from_unit_id,
            MeasurementConversion.to_measurement_unit_id == to_unit_id,
            MeasurementConversion.is_active == True
        ).first()

        if not conversion:
            return None

        return value * conversion.conversion_factor


conversion_service = ConversionService()