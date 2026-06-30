

from decimal import Decimal

import pytest

from fastapi import HTTPException

from app.services.listing_validation_service import (
    listing_validation_service
)

@pytest.mark.asyncio
async def test_invalid_price(
    db_session
):
    with pytest.raises(HTTPException):
        await listing_validation_service.validate_listing_dependencies(
            db=db_session,
            market_id="1",
            product_id="1",
            unit_id="1",
            price=Decimal("0"),
            stock=10
        )


@pytest.mark.asyncio
async def test_invalid_stock(
    db_session
):
    with pytest.raises(HTTPException):
        await listing_validation_service.validate_listing_dependencies(
            db=db_session,
            market_id="1",
            product_id="1",
            unit_id="1",
            price=Decimal("100"),
            stock=0
        )


@pytest.mark.asyncio
async def test_inactive_listing(
    db_session,
    listing
):
    listing.status = "disabled"

    with pytest.raises(HTTPException):
        await listing_validation_service.validate_listing(
            db=db_session,
            listing_id=listing.id
        )


@pytest.mark.asyncio
async def test_out_of_stock_listing(
    db_session,
    listing
):
    listing.available_stock = 0

    with pytest.raises(HTTPException):
        await listing_validation_service.validate_listing(
            db=db_session,
            listing_id=listing.id
        )