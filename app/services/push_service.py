# =========================================
# FILE: app/services/push_service.py
# =========================================

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification
from app.services.outbox_service import outbox_service


class PushService:

    async def send_push(
        self,
        db: AsyncSession,
        user_id: str,
        device_token: str,
        title: str,
        message: str
    ):

        notification = Notification(
            user_id=user_id,
            channel="push",
            title=title,
            message=message,
            status="pending"
        )

        db.add(notification)

        await db.flush()

        await outbox_service.queue_event(
            db=db,
            topic="notification.push.send",
            payload={
                "notification_id": notification.id,
                "device_token": device_token,
                "title": title,
                "message": message
            }
        )

        notification.status = "pending"
        notification.sent_at = datetime.now(timezone.utc)

        return notification


push_service = PushService()