from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db.session import get_db
from decimal import Decimal

from app.services.cooperative_full_procurement_service import (
    CooperativeFullProcurementService
)

from app.db.models.market_product_listing import (
    MarketProductListing
)

from app.db.models.cooperative_procurement import (
    CooperativeProcurement
)


router = APIRouter(
    prefix="/cooperative/procurement",
    tags=["Cooperative Procurement"]
)

service = CooperativeFullProcurementService()


@router.post("/full")
async def create_full_procurement(
    payload: dict,
    db: AsyncSession = Depends(get_db)
):

    listing = await db.get(
        MarketProductListing,
        payload["listing_id"]
    )

    

    raise HTTPException(
        status_code=404,
        detail="Listing not found"
)
    return await service.create_full_procurement(
        db=db,
        cooperative_id=payload["cooperative_id"],
        listing=listing,
        quantity=payload["quantity"],
        total_cost=Decimal(
            str(payload["total_cost"])
        )
    


@router.post("/complete/{procurement_id}")
async def complete_procurement(
    procurement_id: str,
    db: AsyncSession = Depends(get_db)
):

    procurement = await db.get(
        CooperativeProcurement,
        procurement_id
    )

    if not procurement:
        return {
            "status": "procurement_not_found"
        }

    return await service.complete_procurement(
        db=db,
        procurement=procurement
    )