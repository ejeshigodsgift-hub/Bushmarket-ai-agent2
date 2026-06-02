from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.services.cooperative_service import cooperative_service
from app.services.cooperative_membership_service import cooperative_membership_service
from app.services.cooperative_payment_service import cooperative_payment_service

from app.core.auth import get_current_user  # adjust to your auth system

router = APIRouter(prefix="/cooperatives", tags=["Cooperatives"])


# ====================================================
# CREATE COOPERATIVE
# ====================================================
@router.post("/")
def create_cooperative(
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return cooperative_service.create_cooperative(
        db=db,
        creator=current_user,
        data=data,
        ip="system"
    )


# ====================================================
# GET ALL ACTIVE COOPERATIVES
# ====================================================
@router.get("/")
def get_cooperatives(
    db: Session = Depends(get_db)
):

    return cooperative_service.get_active_cooperatives(db)


# ====================================================
# GET SINGLE COOPERATIVE
# ====================================================
@router.get("/{coop_id}")
def get_cooperative(
    coop_id: str,
    db: Session = Depends(get_db)
):

    coop = cooperative_service.get_cooperative(db, coop_id)

    if not coop:
        raise HTTPException(status_code=404, detail="Cooperative not found")

    return coop


# ====================================================
# JOIN COOPERATIVE (INITIATE MEMBERSHIP + PAYMENT)
# ====================================================
@router.post("/{coop_id}/join")
def join_cooperative(
    coop_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # Step 1: create pending membership
    membership = cooperative_membership_service.create_pending_membership(
        db=db,
        user_id=current_user.id,
        cooperative_id=coop_id
    )

    # Step 2: initiate payment
    payment = cooperative_payment_service.initiate_membership_payment(
        db=db,
        user=current_user,
        membership=membership
    )

    return {
        "membership_id": membership.id,
        "status": membership.status,
        "payment": payment
    }


# ====================================================
# GET USER MEMBERSHIP STATUS
# ====================================================
@router.get("/{coop_id}/membership/status")
def get_membership_status(
    coop_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return cooperative_membership_service.get_membership_status(
        db=db,
        user_id=current_user.id,
        cooperative_id=coop_id
    )


# ====================================================
# PAYMENT WEBHOOK (SUCCESS)
# ====================================================
@router.post("/payment/webhook/success")
async def payment_success_webhook(
    request: Request,
    db: Session = Depends(get_db)
):

    payload = await request.json()

    return cooperative_payment_service.handle_payment_success(
        db=db,
        payload=payload
    )


# ====================================================
# PAYMENT WEBHOOK (FAILED)
# ====================================================
@router.post("/payment/webhook/failed")
async def payment_failed_webhook(
    request: Request,
    db: Session = Depends(get_db)
):

    payload = await request.json()

    return cooperative_payment_service.handle_payment_failed(
        db=db,
        payload=payload
    )


# ====================================================
# GET USER COOPERATIVES
# ====================================================
@router.get("/user/me")
def get_my_cooperatives(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return cooperative_membership_service.get_user_cooperatives(
        db=db,
        user_id=current_user.id
    )