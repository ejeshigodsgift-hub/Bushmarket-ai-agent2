from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cooperative import Cooperative
from app.services.outbox_service import outbox_service

class CooperativeStateService:

VALID_TRANSITIONS = {

    "draft": [
        "active",
        "cancelled"
    ],

    "active": [
        "funded",
        "expired",
        "extension_vote",
        "merge_vote",
        "partial_vote",
        "cancelled"
    ],

    "extension_vote": [
        "active",
        "expired",
        "cancelled"
    ],

    "merge_vote": [
        "active",
        "procurement_pending",
        "cancelled"
    ],

    "partial_vote": [
        "procurement_pending",
        "active",
        "cancelled"
    ],

    "funded": [
        "procurement_pending",
        "refunded",
        "cancelled"
    ],

    "procurement_pending": [
        "purchasing",
        "refunded",
        "cancelled"
    ],

    "purchasing": [
        "delivered"
    ],

    "delivered": [
        "closed"
    ],

    "closed": [],
    "expired": [],
    "cancelled": [],
    "refunded": []
}

async def transition(
    self,
    db: AsyncSession,
    cooperative: Cooperative,
    new_state: str,
    reason: str | None = None
):

    current = cooperative.status

    allowed = self.VALID_TRANSITIONS.get(
        current,
        []
    )

    if new_state not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition: {current} -> {new_state}"
        )

    cooperative.status = new_state

    now = datetime.now(timezone.utc)

    if new_state == "funded":
        cooperative.funded_at = now

    elif new_state == "closed":
        cooperative.closed_at = now

    elif new_state == "expired":
        cooperative.expired_at = now

    elif new_state == "cancelled":
        cooperative.cancelled_at = now

    await outbox_service.queue_event(
        db=db,
        topic="cooperative.state.changed",
        payload={
            "cooperative_id": cooperative.id,
            "old_state": current,
            "new_state": new_state,
            "reason": reason
        }
    )

    await db.commit()
    await db.refresh(cooperative)

    return cooperative

cooperative_state_service = CooperativeStateService()