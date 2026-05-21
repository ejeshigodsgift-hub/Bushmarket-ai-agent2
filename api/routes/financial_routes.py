from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from db.session import get_db
from core.security import get_user
from services.payment_service import PaymentService
from services.escrow_service import EscrowService

router = APIRouter()

payment_service = PaymentService()
escrow_service = EscrowService()


# -------------------------
# DEPOSIT MONEY
# -------------------------
@router.post("/wallet/deposit")
def deposit(request: Request, amount: float, db: Session = Depends(get_db)):

    user = get_user(request)
    return payment_service.deposit(db, user["user_id"], amount)


# -------------------------
# ESCROW HOLD (COOPERATIVE JOIN)
# -------------------------
@router.post("/wallet/hold")
def hold(request: Request, coop_id: int, amount: float, db: Session = Depends(get_db)):

    user = get_user(request)
    return escrow_service.hold_funds(db, user["user_id"], coop_id, amount)