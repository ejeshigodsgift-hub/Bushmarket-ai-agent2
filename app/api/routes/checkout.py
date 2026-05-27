from fastapi import APIRouter, Depends, Request, HTTPException

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.cart import Cart

from app.services.checkout_service import CheckoutService


router = APIRouter(prefix="/checkout", tags=["Checkout"])

checkout_service = CheckoutService()


@router.post("/")
def checkout(request: Request, db: Session = Depends(get_db)):

    user = request.state.user

    if not user:
        raise HTTPException(401, "Unauthorized")

    cart = (
        db.query(Cart)
        .filter(
            Cart.user_id == user["id"],
            Cart.status == "active"
        )
        .first()
    )

    if not cart:
        raise HTTPException(404, "Active cart not found")

    checkout = checkout_service.create_checkout(
        db=db,
        user_id=user["id"],
        cart=cart
    )

    return {
        "status": "success",
        "checkout_id": checkout.id,
        "total": checkout.total
    }