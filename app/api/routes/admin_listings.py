from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.market_listing_service import market_listing_service
from app.services.permission_service import PermissionService
from app.services.audit_service import AuditService
from app.services.listing_validation_service import listing_validation_service
from app.services.agent_verification_service import agent_verification_service

router = APIRouter(prefix="/admin/listings")

permission_service = PermissionService()
audit_service = AuditService()


# =========================
# CREATE LISTING (ADMIN/AGENT ONLY)
# =========================
@router.post("/")
def create_listing(payload: dict, request: Request, db: Session = Depends(get_db)):

    user = request.state.user

    if not user:
        raise HTTPException(401, "Unauthorized")

    user_id = user["id"]
    roles = user.get("roles", [])

    # RBAC
    permission_service.validate_permission(roles, "create_listing")

    # AGENT VALIDATION
    if "agent" in roles:
        if not agent_verification_service.is_valid_agent(db, user_id):
            raise HTTPException(403, "Agent not approved")

    # LISTING VALIDATION
    listing_validation_service.validate_listing_dependencies(
        db=db,
        agent_id=user_id,
        market_id=payload["market_id"],
        product_id=payload["product_id"],
        unit_id=payload["measurement_unit_id"],
        price=payload["unit_price"],
        stock=payload["available_stock"]
    )

    # CREATE
    listing = market_listing_service.create_listing(
        db=db,
        agent=user,
        data=payload,
        ip=request.client.host
    )

    # AUDIT
    audit_service.log(
        db=db,
        user_id=user_id,
        action="create_listing",
        entity_type="market_listing",
        entity_id=listing.id,
        metadata=payload,
        ip=request.client.host
    )

    return {
        "status": "success",
        "listing_id": listing.id,
        "status_state": listing.status
    }