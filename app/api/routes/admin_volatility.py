# =========================================
# FILE: app/api/admin/volatility.py
# =========================================

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.market_volatility_rule import MarketVolatilityRule

from app.services.permission_service import PermissionService

router = APIRouter(prefix="/admin/volatility")

permission_service = PermissionService()


# =========================
# CREATE / UPDATE RULE (UPSERT)
# =========================
@router.post("/rule")
def create_or_update_rule(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db)
):

    # =========================================
    # ADMIN AUTH CHECK
    # =========================================
    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    roles = user.get("roles", [])

    # =========================================
    # PERMISSION CHECK
    # =========================================
    permission_service.validate_permission(
        roles,
        "manage_volatility_rules"
    )

    product_id = payload.get("product_id")
    market_id = payload.get("market_id")

    # =========================================
    # UPSERT LOGIC (NO DUPLICATES)
    # =========================================
    rule = db.query(MarketVolatilityRule).filter(
        MarketVolatilityRule.product_id == product_id,
        MarketVolatilityRule.market_id == market_id
    ).first()

    if rule:
        # UPDATE EXISTING RULE
        rule.normal_threshold = payload.get(
            "normal_threshold",
            rule.normal_threshold
        )

        rule.suspicious_threshold = payload.get(
            "suspicious_threshold",
            rule.suspicious_threshold
        )

        rule.critical_threshold = payload.get(
            "critical_threshold",
            rule.critical_threshold
        )

        rule.sensitivity_multiplier = payload.get(
            "sensitivity_multiplier",
            rule.sensitivity_multiplier
        )

        rule.is_active = True

    else:
        # CREATE NEW RULE
        rule = MarketVolatilityRule(
            product_id=product_id,
            market_id=market_id,
            normal_threshold=payload.get("normal_threshold", 0.05),
            suspicious_threshold=payload.get("suspicious_threshold", 0.15),
            critical_threshold=payload.get("critical_threshold", 0.30),
            sensitivity_multiplier=payload.get("sensitivity_multiplier", 1.0),
            is_active=True
        )

        db.add(rule)

    db.commit()
    db.refresh(rule)

    return {
        "rule_id": str(rule.id),
        "status": "saved",
        "mode": "updated" if rule else "created"
    }


# =========================
# VIEW RULES
# =========================
@router.get("/rules")
def get_rules(
    request: Request,
    db: Session = Depends(get_db)
):

    # =========================================
    # ADMIN AUTH CHECK
    # =========================================
    user = request.state.user

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    roles = user.get("roles", [])

    permission_service.validate_permission(
        roles,
        "manage_volatility_rules"
    )

    return db.query(MarketVolatilityRule).all()