from fastapi import (
    APIRouter,
    Depends,
    Request
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.services.cart_service import CartService


router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)

cart_service = CartService()


# =========================
# ADD TO CART
# =========================

@router.post("/add")

def add_to_cart(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db)
):

    user = request.state.user

    if not user:
        return {
            "status": "failed",
            "message": "Unauthorized"
        }

    item = cart_service.add_to_cart(
        db=db,
        user_id=user["user_id"],
        listing_id=payload["listing_id"],
        quantity=payload["quantity"],
        ip_address=request.client.host
    )

    return {
        "status": "success",
        "cart_item_id": item.id
    }