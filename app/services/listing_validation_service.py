# =========================================
# FILE: app/services/listing_validation_service.py
# =========================================

from decimal import Decimal

from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.market_location import MarketLocation
from app.db.models.market_product_listing import MarketProductListing
from app.db.models.measurement_unit import MeasurementUnit
from app.db.models.product import Product


class ListingValidationService:

    # =========================================
    # VALIDATE DEPENDENCIES
    # =========================================
    async def validate_listing_dependencies(
        self,
        db: AsyncSession,
        market_id: str,
        product_id: str,
        unit_id: str,
        price: Decimal,
        stock: int
    ) -> bool:

        if Decimal(price) <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid listing price"
            )

        if stock <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid stock quantity"
            )

        # product
        product_result = await db.execute(
            select(Product)
            .where(
                Product.id == product_id,
                Product.is_active.is_(True)
            )
            .limit(1)
        )

        product = product_result.scalar_one_or_none()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        # market
        market_result = await db.execute(
            select(MarketLocation)
            .where(
                MarketLocation.id == market_id,
                MarketLocation.is_active.is_(True)
            )
            .limit(1)
        )

        market = market_result.scalar_one_or_none()

        if not market:
            raise HTTPException(
                status_code=404,
                detail="Market not found"
            )

        # measurement unit
        unit_result = await db.execute(
            select(MeasurementUnit)
            .where(
                MeasurementUnit.id == unit_id,
                MeasurementUnit.is_active.is_(True)
            )
            .limit(1)
        )

        unit = unit_result.scalar_one_or_none()

        if not unit:
            raise HTTPException(
                status_code=404,
                detail="Measurement unit not found"
            )

        return True

    # =========================================
    # RUNTIME VALIDATION
    # =========================================
    async def validate_listing(
        self,
        db: AsyncSession,
        listing_id: str
    ) -> MarketProductListing:

        stmt = (
            select(MarketProductListing)
            .options(
                selectinload(MarketProductListing.agent),
                selectinload(MarketProductListing.product),
                selectinload(MarketProductListing.market),
                selectinload(MarketProductListing.measurement_unit)
            )
            .where(
                MarketProductListing.id == listing_id
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        listing = result.scalar_one_or_none()

        if not listing:
            raise HTTPException(
                status_code=404,
                detail="Listing not found"
            )

        if listing.status != "active":
            raise HTTPException(
                status_code=400,
                detail="Listing inactive"
            )

        if listing.available_stock <= 0:
            raise HTTPException(
                status_code=400,
                detail="Out of stock"
            )

        if Decimal(listing.unit_price) <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid listing price"
            )

        if not listing.agent:
            raise HTTPException(
                status_code=400,
                detail="Assigned agent missing"
            )

        if not listing.agent.is_verified_agent:
            raise HTTPException(
                status_code=403,
                detail="Agent not verified"
            )

        return listing


listing_validation_service = ListingValidationService()