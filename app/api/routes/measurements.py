from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.measurement_service import measurement_service


router = APIRouter(prefix="/measurements")


# =========================
# GET PRODUCT MEASUREMENTS
# =========================
@router.get("/product/{product_id}")
def get_product_measurements(
    product_id: str,
    db: Session = Depends(get_db)
):

    return measurement_service.get_product_measurements(
        db,
        product_id
    )