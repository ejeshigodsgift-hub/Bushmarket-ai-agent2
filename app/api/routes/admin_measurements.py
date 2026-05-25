from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.measurement_service import measurement_service
from app.services.permission_service import PermissionService


router = APIRouter(prefix="/admin/measurements")

permission_service = PermissionService()


# =========================
# CREATE UNIT
# =========================
@router.post("/")
def create_measurement_unit(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(status_code=401)

    permission_service.validate_permission(
        user.get("roles", []),
        "*"
    )

    unit = measurement_service.create_measurement_unit(
        db,
        payload
    )

    return {
        "measurement_unit_id": unit.id
    }