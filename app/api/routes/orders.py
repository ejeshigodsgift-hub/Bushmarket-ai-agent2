from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from pydantic import BaseModel

from app.services.wallet_payment_service import (
    wallet_payment_service
)

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
    db: AsyncSession = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    result = await db.execute(
        select(Cart).where(
            Cart.user_id == user["id"],
            Cart.status == "active"
        )
    )

    cart = result.scalar_one_or_none()


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



class WalletPaymentRequest(BaseModel):
    order_id: str
    wallet_id: str

@router.post("/pay-with-wallet")
async def pay_with_wallet(
    payload: WalletPaymentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    result = await wallet_payment_service.pay_order_with_wallet(
        db=db,
        user_id=user["id"],
        order_id=payload.order_id,
        wallet_id=payload.wallet_id,
        reference=f"WALLET-ORDER-{payload.order_id}"
    )

    return {
        "status": "success",
        "order_id": result.id
    }