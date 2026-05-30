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
from app.db.models.user import User


class ListingValidationService:

    # =========================================
    # VALIDATE DEPENDENCIES (CREATE LISTING)
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

        # -----------------------------
        # PRICE VALIDATION
        # -----------------------------
        if Decimal(price) <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid listing price"
            )

        # -----------------------------
        # STOCK VALIDATION
        # -----------------------------
        if stock <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid stock quantity"
            )

        # -----------------------------
        # PRODUCT CHECK
        # -----------------------------
        product_result = await db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.is_active.is_(True)
            ).limit(1)
        )

        product = product_result.scalar_one_or_none()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found or inactive"
            )

        # -----------------------------
        # MARKET CHECK
        # -----------------------------
        market_result = await db.execute(
            select(MarketLocation).where(
                MarketLocation.id == market_id,
                MarketLocation.is_active.is_(True)
            ).limit(1)
        )

        market = market_result.scalar_one_or_none()

        if not market:
            raise HTTPException(
                status_code=404,
                detail="Market not found or inactive"
            )

        # -----------------------------
        # MEASUREMENT UNIT CHECK
        # -----------------------------
        unit_result = await db.execute(
            select(MeasurementUnit).where(
                MeasurementUnit.id == unit_id,
                MeasurementUnit.is_active.is_(True)
            ).limit(1)
        )

        unit = unit_result.scalar_one_or_none()

        if not unit:
            raise HTTPException(
                status_code=404,
                detail="Measurement unit not found or inactive"
            )

        return True

    # =========================================
    # RUNTIME VALIDATION (LISTING USAGE)
    # =========================================
    async def validate_listing(
        self,
        db: AsyncSession,
        listing_id: str
    ) -> MarketProductListing:

        stmt = (
            select(MarketProductListing)
            .options(
                selectinload(MarketProductListing.assigned_agent),
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

        # -----------------------------
        # STATUS CHECK
        # -----------------------------
        if listing.status != "active":
            raise HTTPException(
                status_code=400,
                detail="Listing is not active"
            )

        # -----------------------------
        # STOCK CHECK
        # -----------------------------
        if listing.available_stock <= 0:
            raise HTTPException(
                status_code=400,
                detail="Out of stock"
            )

        # -----------------------------
        # PRICE CHECK
        # -----------------------------
        if Decimal(listing.unit_price) <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid listing price"
            )

        # -----------------------------
        # ASSIGNED AGENT CHECK (FIXED LOGIC)
        # CRITICAL FIX:
        # use assigned_agent, NOT generic agent
        # -----------------------------
        if not listing.assigned_agent_id:
            raise HTTPException(
                status_code=400,
                detail="Assigned agent missing"
            )

        if not listing.assigned_agent:
            raise HTTPException(
                status_code=400,
                detail="Assigned agent not loaded"
            )

        if not listing.assigned_agent.is_verified_agent:
            raise HTTPException(
                status_code=403,
                detail="Assigned agent not verified"
            )

        # -----------------------------
        # OPTIONAL SAFETY CHECK (alignment guard)
        # ensures DB integrity between FK and relationship
        # -----------------------------
        if listing.assigned_agent.id != listing.assigned_agent_id:
            raise HTTPException(
                status_code=500,
                detail="Agent assignment mismatch detected"
            )

        return listing


listing_validation_service = ListingValidationService()