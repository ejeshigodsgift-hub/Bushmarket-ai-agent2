from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.product_service import product_service


router = APIRouter(prefix="/products")


# =========================
# SEARCH PRODUCTS
# =========================
@router.get("/search")
def search_products(
    keyword: str,
    db: Session = Depends(get_db)
):

    products = product_service.search_products(
        db,
        keyword
    )

    return products