# =========================================
# FILE: app/api/admin/volatility.py
# =========================================

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.market_volatility_rule import MarketVolatilityRule
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/admin/volatility")

permission_service = PermissionService()


# =========================
# CREATE / UPDATE RULE (UPSERT)
# =========================
@router.post("/rule")
async def create_or_update_rule(
    payload: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

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

    product_id = payload.get("product_id")
    market_id = payload.get("market_id")

    stmt = select(MarketVolatilityRule).where(
        MarketVolatilityRule.product_id == product_id,
        MarketVolatilityRule.market_id == market_id
    )

    result = await db.execute(stmt)
    rule = result.scalar_one_or_none()

    if rule:
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

        mode = "updated"

    else:
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

        mode = "created"

    await db.commit()
    await db.refresh(rule)

    return {
        "rule_id": str(rule.id),
        "status": "saved",
        "mode": mode
    }


# =========================
# VIEW RULES
# =========================
@router.get("/rules")
async def get_rules(
    request: Request,
    db: AsyncSession = Depends(get_db)
):

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

    stmt = select(MarketVolatilityRule)

    result = await db.execute(stmt)

    return result.scalars().all()