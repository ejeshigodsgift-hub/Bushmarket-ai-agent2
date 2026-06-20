from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.cart import Cart

from app.services.checkout_service import CheckoutService


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

checkout_service = CheckoutService()


@router.post("/checkout")
async def checkout(
    request: Request,
    db: Session = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    cart = (
        db.query(Cart)
        .filter(
            Cart.user_id == user["id"],
            Cart.status == "active"
        )
        .first()
    )

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Active cart not found"
        )

    checkout = await checkout_service.create_checkout(
        db=db,
        user_id=user["id"],
        cart=cart
    )

    return {
        "status": "success",
        "checkout_id": checkout.id,
        "total": str(checkout.total),
        "expires_at": checkout.expires_at.isoformat()
    }