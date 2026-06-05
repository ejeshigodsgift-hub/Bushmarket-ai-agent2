# =========================================
# FILE: app/services/sms_service.py
# =========================================

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification
from app.services.outbox_service import outbox_service


class SMSService:

    async def send_sms(
        self,
        db: AsyncSession,
        user_id: str,
        phone_number: str,
        message: str
    ):

        notification = Notification(
            user_id=user_id,
            channel="sms",
            title="SMS Notification",
            message=message,
            status="pending"
        )

        db.add(notification)

        await outbox_service.queue_event(
            db=db,
            topic="notification.sms.send",
            payload={
                "notification_id": notification.id,
                "phone_number": phone_number,
                "message": message
            }
        )

        notification.status = "sent"
        notification.sent_at = datetime.now(timezone.utc)

        return notification


sms_service = SMSService()