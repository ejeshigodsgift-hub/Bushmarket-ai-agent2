from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.market_volatility_rule import MarketVolatilityRule

router = APIRouter(prefix="/admin/volatility")


# =========================
# CREATE / UPDATE RULE
# =========================
@router.post("/rule")
def create_or_update_rule(payload: dict, db: Session = Depends(get_db)):

    rule = MarketVolatilityRule(
        product_id=payload.get("product_id"),
        market_id=payload.get("market_id"),
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
        "rule_id": rule.id,
        "status": "saved"
    }


# =========================
# VIEW RULES
# =========================
@router.get("/rules")
def get_rules(db: Session = Depends(get_db)):

    return db.query(MarketVolatilityRule).all()