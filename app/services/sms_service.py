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
        notification: Notification,
        phone_number: str
    ):

        
        
        await outbox_service.queue_event(
            db=db,
            topic="notification.sms.send",
            payload={
                "notification_id": notification.id,
                "phone_number": phone_number,
                "message": notification.message
            }
        )

        
        return notification


sms_service = SMSService()