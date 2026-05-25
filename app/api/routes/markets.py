from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.market_service import market_service


router = APIRouter(prefix="/markets")


# =========================
# GET ALL MARKETS
# =========================
@router.get("/")
def get_markets(
    db: Session = Depends(get_db)
):

    return market_service.get_markets(db)