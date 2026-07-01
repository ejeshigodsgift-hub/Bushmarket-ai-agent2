from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.services.cooperative_service import cooperative_service
from app.services.cooperative_membership_service import (
cooperative_membership_service
)
from app.services.cooperative_payment_service import (
cooperative_payment_service
)

from app.core.auth import get_current_user

router = APIRouter(
prefix="/cooperatives",
tags=["Cooperatives"]
)

====================================================

CREATE COOPERATIVE

====================================================

@router.post("/")
async def create_cooperative(
data: dict,
db: AsyncSession = Depends(get_db),
current_user=Depends(get_current_user)
):
return await cooperative_service.create_cooperative(
db=db,
creator=current_user,
data=data,
ip="system"
)

====================================================

GET ALL ACTIVE COOPERATIVES

====================================================

@router.get("/")
async def get_cooperatives(
db: AsyncSession = Depends(get_db)
):
return await cooperative_service.get_active_cooperatives(
db
)

====================================================

GET SINGLE COOPERATIVE

====================================================

@router.get("/{coop_id}")
async def get_cooperative(
coop_id: str,
db: AsyncSession = Depends(get_db)
):
coop = await cooperative_service.get_cooperative(
db,
coop_id
)

if not coop:
    raise HTTPException(
        status_code=404,
        detail="Cooperative not found"
    )

return coop

====================================================

JOIN COOPERATIVE

====================================================

@router.post("/{coop_id}/join")
async def join_cooperative(
coop_id: str,
db: AsyncSession = Depends(get_db),
current_user=Depends(get_current_user)
):

membership = await cooperative_membership_service.create_pending_membership(
    db=db,
    user_id=current_user.id,
    cooperative_id=coop_id
)

payment = await cooperative_payment_service.initiate_membership_payment(
    db=db,
    user=current_user,
    membership=membership
)

return {
    "membership_id": membership.id,
    "status": membership.status,
    "payment": payment
}

====================================================

MEMBERSHIP STATUS

====================================================

@router.get("/{coop_id}/membership/status")
async def get_membership_status(
coop_id: str,
db: AsyncSession = Depends(get_db),
current_user=Depends(get_current_user)
):
return await cooperative_membership_service.get_membership_status(
db=db,
user_id=current_user.id,
cooperative_id=coop_id
)

====================================================

PAYMENT SUCCESS WEBHOOK

====================================================

@router.post("/payment/webhook/success")
async def payment_success_webhook(
request: Request,
db: AsyncSession = Depends(get_db)
):
payload = await request.json()

return await cooperative_payment_service.handle_payment_success(
    db=db,
    payload=payload
)

====================================================

PAYMENT FAILED WEBHOOK

====================================================

@router.post("/payment/webhook/failed")
async def payment_failed_webhook(
request: Request,
db: AsyncSession = Depends(get_db)
):
payload = await request.json()

return await cooperative_payment_service.handle_payment_failed(
    db=db,
    payload=payload
)

====================================================

MY COOPERATIVES

====================================================

@router.get("/user/me")
async def get_my_cooperatives(
db: AsyncSession = Depends(get_db),
current_user=Depends(get_current_user)
):
return await cooperative_membership_service.get_user_cooperatives(
db=db,
user_id=current_user.id
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

