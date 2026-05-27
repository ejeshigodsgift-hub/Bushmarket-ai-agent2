from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.db.models.cart import Cart

from app.services.order_service import OrderService


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

order_service = OrderService()


@router.post("/checkout")
def checkout(
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

    order = order_service.create_order(
        db=db,
        user_id=user["id"],
        cart=cart
    )

    return {
        "status": "success",
        "order_id": order.id,
        "order_number": order.order_number
    }