from datetime import datetime, timezone

from fastapi import HTTPException

from app.services.cooperative_service import cooperative_service
from app.services.cooperative_message_service import (
    cooperative_message_service
)


class CooperativeAIService:

    async def get_status(
        self,
        db,
        user_id: str,
        cooperative_id: str
    ):

        cooperative = await cooperative_service.get_by_id(
            db=db,
            cooperative_id=cooperative_id
        )

        if not cooperative:
            raise HTTPException(
                status_code=404,
                detail="Cooperative not found"
            )

        await cooperative_service.require_member(
            db=db,
            cooperative_id=cooperative_id,
            user_id=user_id
        )

        member_count = len(cooperative.members)

        now = datetime.now(timezone.utc)

        days_remaining = 0

        if cooperative.expires_at:
            delta = cooperative.expires_at - now
            days_remaining = max(delta.days, 0)

        return {
            "cooperative_id": cooperative.id,
            "cooperative_name": cooperative.name,
            "member_count": member_count,
            "target_members": cooperative.target_members,
            "target_quantity": cooperative.target_quantity,
            "current_quantity": cooperative.current_quantity,
            "days_remaining": days_remaining,
            "status": cooperative.status,
            "reply": (
                f"{cooperative.name} has "
                f"{member_count} members and "
                f"{days_remaining} days remaining."
            )
        }

    async def send_reminder(
        self,
        db,
        user_id: str,
        cooperative_id: str
    ):

        cooperative = await cooperative_service.get_by_id(
            db=db,
            cooperative_id=cooperative_id
        )

        if not cooperative:
            raise HTTPException(
                status_code=404,
                detail="Cooperative not found"
            )

        await cooperative_service.require_member(
            db=db,
            cooperative_id=cooperative_id,
            user_id=user_id
        )

        sent = await cooperative_message_service.send_to_members(
            db=db,
            cooperative_id=cooperative_id,
            sender_user_id=user_id,
            title="Cooperative Reminder",
            message=(
                "Please review cooperative status. "
                "You may need to extend lifespan "
                "or vote for partial procurement."
            )
        )

        return {
            "success": True,
            "messages_sent": sent,
            "reply": (
                f"Reminder sent to "
                f"{sent} cooperative members."
            )
        }


cooperative_ai_service = CooperativeAIService()