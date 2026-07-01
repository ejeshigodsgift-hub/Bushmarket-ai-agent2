from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.services.cooperative_full_procurement_service import (
    CooperativeFullProcurementService
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
    return await service.create_full_procurement(
        db=db,
        cooperative_id=payload["cooperative_id"],
        listing=payload["listing"],
        quantity=payload["quantity"],
        total_cost=payload["total_cost"]
    )


@router.post("/complete/{procurement_id}")
async def complete_procurement(
    procurement_id: str,
    db: AsyncSession = Depends(get_db)
):
    procurement = await db.get(
        service.__annotations__.get(
            "CooperativeProcurement",
            object
        ),
        procurement_id
    )

    return await service.complete_procurement(
        db=db,
        procurement=procurement
    )