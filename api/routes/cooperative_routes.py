from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from db.session import get_db
from core.security import get_user_from_cookie
from schemas.cooperative import CooperativeCreate
from schemas.membership import JoinCooperative
from services.cooperative_service import CooperativeService
from repositories.cooperative_repo import CooperativeRepository

router = APIRouter()
service = CooperativeService()
repo = CooperativeRepository()


# -------------------------
# CREATE COOPERATIVE
# -------------------------
@router.post("/cooperative/create")
def create_coop(
    data: CooperativeCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_user_from_cookie(request)
    return service.create_cooperative(db, user["user_id"], data)


# -------------------------
# JOIN COOPERATIVE
# -------------------------
@router.post("/cooperative/join")
def join_coop(
    data: JoinCooperative,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_user_from_cookie(request)
    coop = repo.get(db, data.cooperative_id)

    if not coop:
        return {"error": "Cooperative not found"}

    return service.join_cooperative(db, user["user_id"], coop)