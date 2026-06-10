from decimal import Decimal
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.db.models.cooperative_procurement import CooperativeProcurement


class CooperativeMergeProcurementService:

    def merge_procurements(
        self,
        db: Session,
        cooperative_id: str,
        procurements: List[CooperativeProcurement],
    ) -> CooperativeProcurement:

        if not procurements:
            raise ValueError("No procurements to merge")

        total_quantity = sum(p.procurement_quantity for p in procurements)
        total_value = sum(p.procurement_value for p in procurements)

        merged = CooperativeProcurement(
            cooperative_id=cooperative_id,
            procurement_type="merged",
            procurement_quantity=total_quantity,
            procurement_value=total_value,
            estimated_retail_value=sum(p.estimated_retail_value for p in procurements),
            cooperative_buying_value=total_value,
            estimated_savings=sum(p.estimated_savings for p in procurements),
            savings_percentage=Decimal("0"),
            status="approved",
            approved_at=datetime.utcnow()
        )

        db.add(merged)

        for p in procurements:
            p.status = "merged"

        db.commit()
        db.refresh(merged)

        return merged

    def finalize_merge(self, db: Session, merged: CooperativeProcurement):
        merged.status = "completed"
        merged.completed_at = datetime.utcnow()
        db.commit()
        return merged