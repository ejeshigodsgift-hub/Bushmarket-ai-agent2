# =========================================
# FILE: app/services/conversion_service.py
# =========================================

from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.measurement_conversion import MeasurementConversion


class ConversionService:
    """
    Handles measurement conversion logic.

    Production Features:
    - Async SQLAlchemy 2.0
    - Decimal-safe arithmetic
    - Active-rule enforcement
    - Scalable conversion lookup
    """

    async def convert(
        self,
        db: AsyncSession,
        from_unit_id: str,
        to_unit_id: str,
        value: Decimal
    ) -> Optional[Decimal]:

        # same unit shortcut
        if from_unit_id == to_unit_id:
            return value

        stmt = (
            select(MeasurementConversion)
            .where(
                MeasurementConversion.from_measurement_unit_id == from_unit_id,
                MeasurementConversion.to_measurement_unit_id == to_unit_id,
                MeasurementConversion.is_active.is_(True)
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        conversion = result.scalar_one_or_none()

        if not conversion:
            return None

        return Decimal(value) * Decimal(conversion.conversion_factor)


conversion_service = ConversionService()