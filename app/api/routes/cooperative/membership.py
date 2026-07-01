from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.cooperative_membership_service import (
    cooperative_membership_service
)

router = APIRouter(
    prefix="/cooperative/membership",
    tags=["Cooperative Membership"]
)


@router.post("/join/{cooperative_id}")
async def join_cooperative(
    cooperative_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user

    return await cooperative_membership_service.join_cooperative(
        db=db,
        user_id=user["id"],
        cooperative_id=cooperative_id,
        ip=request.client.host
    )


@router.post("/activate/{membership_id}")
async def activate_membership(
    membership_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await cooperative_membership_service.activate_membership(
        db=db,
        membership_id=membership_id
    )


@router.get("/status/{cooperative_id}")
async def membership_status(
    cooperative_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user

    return await cooperative_membership_service.get_membership_status(
        db=db,
        user_id=user["id"],
        cooperative_id=cooperative_id
    )