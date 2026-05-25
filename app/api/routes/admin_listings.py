from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.services.market_listing_service import (
    market_listing_service
)

from app.services.permission_service import (
    PermissionService
)

from app.services.agent_verification_service import (
    agent_verification_service
)

from app.services.listing_validation_service import (
    listing_validation_service
)

from app.services.listing_guard_service import (
    listing_guard_service
)

from app.services.audit_service import (
    AuditService
)

router = APIRouter(
    prefix="/admin/listings",
    tags=["Admin Listings"]
)

permission_service = PermissionService()

audit_service = AuditService()


# =========================
# CREATE MARKET LISTING
# =========================
@router.post("/")
def create_listing(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db)
):

    # =========================
    # AUTHENTICATION CHECK
    # =========================
    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    user_id = user.get("id")

    roles = user.get("roles", [])

    # =========================
    # GLOBAL RBAC VALIDATION
    # =========================
    permission_service.validate_permission(
        roles,
        "*"
    )

    # =========================
    # LISTING ACCESS CONTROL
    # =========================
    listing_guard_service.enforce_listing_permission(
        roles
    )

    # =========================
    # VERIFIED AGENT CHECK
    # =========================
    if "agent" in roles:

        is_valid_agent = (
            agent_verification_service.is_valid_agent(
                db=db,
                user_id=user_id
            )
        )

        if not is_valid_agent:
            raise HTTPException(
                status_code=403,
                detail="Agent not approved"
            )

    # =========================
    # LISTING VALIDATION
    # =========================
    listing_validation_service.validate_listing_dependencies(
        db=db,
        agent_id=user_id,
        market_id=payload["market_id"],
        product_id=payload["product_id"],
        unit_id=payload["measurement_unit_id"],
        price=payload["unit_price"],
        stock=payload["available_stock"]
    )

    # =========================
    # CREATE MARKET LISTING
    # =========================
    listing_payload = {
        **payload,
        "assigned_agent_id": user_id,
        "status": "active"
    }

    listing = market_listing_service.create_listing(
        db=db,
        payload=listing_payload
    )

    # =========================
    # AUDIT LOGGING
    # =========================
    audit_service.log(
        db=db,
        user_id=user_id,
        action="create_market_listing",
        entity_type="market_listing",
        entity_id=listing.id,
        metadata={
            "market_id": payload["market_id"],
            "product_id": payload["product_id"],
            "measurement_unit_id": payload["measurement_unit_id"]
        },
        ip=request.client.host
    )

    # =========================
    # RESPONSE
    # =========================
    return {
        "status": "success",
        "listing_id": listing.id,
        "listing_status": listing.status
    }