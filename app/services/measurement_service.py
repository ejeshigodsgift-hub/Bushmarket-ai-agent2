# =========================================
# FILE: app/services/measurement_service.py
# =========================================

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from app.db.models.measurement_unit import (
    MeasurementUnit
)

from app.db.models.product_measurement import (
    ProductMeasurement
)

from app.db.models.measurement_conversion import (
    MeasurementConversion
)


class MeasurementService:

    # =========================================
    # CREATE UNIT
    # =========================================
    async def create_measurement_unit(
        self,
        db: AsyncSession,
        payload: dict
    ) -> MeasurementUnit:

        stmt = (
            select(MeasurementUnit)
            .where(
                MeasurementUnit.name == payload["name"]
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Measurement unit already exists"
            )

        unit = MeasurementUnit(
            name=payload["name"],
            symbol=payload["symbol"],
            unit_type=payload["unit_type"],
            is_active=True
        )

        db.add(unit)

        await db.commit()

        await db.refresh(unit)

        return unit

    # =========================================
    # ASSIGN PRODUCT MEASUREMENT
    # =========================================
    async def assign_product_measurement(
        self,
        db: AsyncSession,
        payload: dict
    ) -> ProductMeasurement:

        stmt = (
            select(ProductMeasurement)
            .where(
                ProductMeasurement.product_id == payload["product_id"],
                ProductMeasurement.measurement_unit_id == payload["measurement_unit_id"]
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        existing = result.scalar_one_or_none()

        if existing:
            return existing

        measurement = ProductMeasurement(
            product_id=payload["product_id"],
            measurement_unit_id=payload["measurement_unit_id"],
            is_default=payload.get("is_default", False)
        )

        db.add(measurement)

        await db.commit()

        await db.refresh(measurement)

        return measurement

    # =========================================
    # CREATE CONVERSION
    # =========================================
    async def create_conversion(
        self,
        db: AsyncSession,
        payload: dict
    ) -> MeasurementConversion:

        if (
            payload["from_measurement_unit_id"]
            == payload["to_measurement_unit_id"]
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid conversion units"
            )

        conversion = MeasurementConversion(
            from_measurement_unit_id=payload[
                "from_measurement_unit_id"
            ],
            to_measurement_unit_id=payload[
                "to_measurement_unit_id"
            ],
            conversion_factor=payload[
                "conversion_factor"
            ],
            is_active=True
        )

        db.add(conversion)

        await db.commit()

        await db.refresh(conversion)

        return conversion

    # =========================================
    # GET PRODUCT MEASUREMENTS
    # =========================================
    async def get_product_measurements(
        self,
        db: AsyncSession,
        product_id: str
    ):

        stmt = (
            select(ProductMeasurement)
            .where(
                ProductMeasurement.product_id == product_id
            )
        )

        result = await db.execute(stmt)

        return result.scalars().all()


measurement_service = MeasurementService()