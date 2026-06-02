from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.cooperative_service import cooperative_service

router = APIRouter(prefix="/cooperatives", tags=["Cooperatives"])


# ====================================================
# CREATE COOPERATIVE
# ====================================================
@router.post("/")
def create_cooperative(
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(...)
):

    return cooperative_service.create_cooperative(
        db=db,
        creator=current_user,
        data=data,
        ip="0.0.0.0"
    )


# ====================================================
# GET ALL ACTIVE
# ====================================================
@router.get("/")
def get_cooperatives(db: Session = Depends(get_db)):

    return cooperative_service.get_active_cooperatives(db)


# ====================================================
# GET SINGLE COOPERATIVE
# ====================================================
@router.get("/{coop_id}")
def get_cooperative(coop_id: str, db: Session = Depends(get_db)):

    return cooperative_service.get_cooperative(db, coop_id)


# ====================================================
# JOIN COOPERATIVE
# ====================================================
@router.post("/{coop_id}/join")
def join_cooperative(
    coop_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(...)
):

    return cooperative_service.join_cooperative(
        db=db,
        user=current_user,
        coop_id=coop_id,
        ip="0.0.0.0"
    )