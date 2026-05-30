# =========================================
# FILE: app/api/admin/listings.py
# =========================================

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.market_listing_service import market_listing_service
from app.services.permission_service import PermissionService
from app.services.audit_service import AuditService
from app.services.agent_verification_service import agent_verification_service

router = APIRouter(prefix="/admin/listings")

permission_service = PermissionService()
audit_service = AuditService()


# =========================
# CREATE LISTING (STRICT AGENT ONLY)
# =========================
@router.post("/")
async def create_listing(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user["id"]
    roles = user.get("roles", [])

    # =====================================
    # RBAC CHECK
    # =====================================
    permission_service.validate_permission(roles, "create_listing")

    # =====================================
    # CRITICAL FIX:
    # ONLY APPROVED AGENTS CAN CREATE LISTINGS
    # =====================================
    is_agent_role = "agent" in roles

    if not is_agent_role:
        raise HTTPException(
            status_code=403,
            detail="Only approved agents can create listings"
        )

    if not agent_verification_service.is_valid_agent(db, user_id):
        raise HTTPException(
            status_code=403,
            detail="Agent not approved"
        )

    # =====================================
    # SERVICE CALL (NO DUPLICATE VALIDATION)
    # Validation is now handled INSIDE service layer
    # =====================================
    listing = await market_listing_service.create_listing(
        db=db,
        agent=user,
        data=payload,
        ip=request.client.host
    )

    # =====================================
    # AUDIT LOG
    # =====================================
    audit_service.log(
        db=db,
        user_id=user_id,
        action="create_listing",
        entity_type="market_listing",
        entity_id=listing.id,
        metadata={
            "listing_id": str(listing.id),
            "market_id": payload["market_id"]
        },
        ip=request.client.host
    )

    return {
        "status": "success",
        "listing_id": str(listing.id),
        "status_state": listing.status
    }