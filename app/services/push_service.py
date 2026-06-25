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
        notification: Notification,
        device_token: str
    ):
        

        await outbox_service.queue_event(
            db=db,
            topic="notification.push.send",
            payload={
                "notification_id": notification.id,
                "device_token": device_token,
                "title": title,
                "message": notification.message
            }
        )

        

        return notification


push_service = PushService()