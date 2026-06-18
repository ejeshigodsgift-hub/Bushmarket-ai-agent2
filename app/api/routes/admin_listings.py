# =========================================
# FILE: app/api/admin/listings.py
# =========================================

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.db.models.listing_agent_activity import ListingAgentActivity

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



# =========================
# APPROVE LISTING
# =========================
@router.post("/{listing_id}/approve")
async def approve_listing(
    listing_id: str,
    request: Request,
    db: Session = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    roles = user.get("roles", [])
    permission_service.validate_permission(roles, "approve_listing")

    listing = await market_listing_service.get_listing(db, listing_id)

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    #listing.status = "active"

    # =========================================
    # LISTING ACTIVITY LOG
    # =========================================
   # db.add(
        #ListingAgentActivity(
           # listing_id=listing.id,
           # agent_id=listing.agent_id,
           # action_type="admin_approved"
      #  )
  #  )


     return await  admin_service.approve_listing(
        db=db,
        listing_id=listing_id,
        admin_id=user["id"]
    )       

    audit_service.log(
        db=db,
        user_id=user["id"],
        action="approve_listing",
        entity_type="market_listing",
        entity_id=listing.id
    )

    await db.commit()

    return {
        "status": "approved",
        "listing_id": str(listing.id)
    }



# =========================
# REJECT LISTING
# =========================
@router.post("/{listing_id}/reject")
async def reject_listing(
    listing_id: str,
    request: Request,
    db: Session = Depends(get_db)
):

    user = request.state.user

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    roles = user.get("roles", [])
    permission_service.validate_permission(roles, "reject_listing")

    listing = await market_listing_service.get_listing(db, listing_id)

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing.status = "rejected"

    # =========================================
    # LISTING ACTIVITY LOG
    # =========================================
    db.add(
        ListingAgentActivity(
            listing_id=listing.id,
            agent_id=listing.agent_id,
            action_type="admin_rejected"
        )
    )

    audit_service.log(
        db=db,
        user_id=user["id"],
        action="reject_listing",
        entity_type="market_listing",
        entity_id=listing.id
    )

    await db.commit()

    return {
        "status": "rejected",
        "listing_id": str(listing.id)
    }
