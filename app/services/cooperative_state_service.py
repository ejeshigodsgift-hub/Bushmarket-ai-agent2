from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.outbox_service import outbox_service


class CooperativeStateEngine:
    """
    CENTRALIZED + ENFORCED COOPERATIVE STATE MACHINE

    Guarantees:
    - No direct status mutation allowed outside apply_transition()
    - All transitions are validated
    - All transitions are observable (outbox event)
    - Single source of truth for state graph
    """

    VALID_TRANSITIONS = {
        "draft": ["active", "cancelled"],

        "active": [
            "funded",
            "expired",
            "extension_vote",
            "merge_vote",
            "partial_vote",
            "cancelled"
        ],

        "extension_vote": ["active", "expired", "cancelled"],
        "merge_vote": ["active", "procurement_pending", "cancelled"],
        "partial_vote": ["procurement_pending", "active", "cancelled"],

        "funded": ["procurement_pending", "refunded", "cancelled"],
        "procurement_pending": ["purchasing", "refunded", "cancelled"],
        "purchasing": ["delivered"],
        "delivered": ["closed"],

        "closed": [],
        "expired": [],
        "cancelled": [],
        "refunded": []
    }

    # ====================================================
    # VALIDATION (PURE RULE ENGINE)
    # ====================================================
    @staticmethod
    def validate_transition(current: str, new: str):
        allowed = CooperativeStateEngine.VALID_TRANSITIONS.get(current, [])

        if new not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transition: {current} → {new}"
            )

    # ====================================================
    # INTERNAL TRANSITION (NO DB, NO SIDE EFFECT)
    # ====================================================
    @staticmethod
    def _transition(coop, new_state: str):
        CooperativeStateEngine.validate_transition(coop.status, new_state)
        coop.status = new_state
        return coop

    # ====================================================
    # SAFE PUBLIC ENTRY (DB + OUTBOX + GUARANTEE)
    # ====================================================
    @staticmethod
    async def apply_transition(
        db: AsyncSession,
        coop,
        new_state: str,
        reason: str | None = None
    ):
        old_state = coop.status

        CooperativeStateEngine._transition(coop, new_state)

        await outbox_service.queue_event(
            db=db,
            topic="cooperative.state.changed",
            payload={
                "cooperative_id": coop.id,
                "old_state": old_state,
                "new_state": new_state,
                "reason": reason
            }
        )

        return coop