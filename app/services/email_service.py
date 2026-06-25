# =========================================
# FILE: app/services/email_service.py
# =========================================

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification
from app.services.outbox_service import outbox_service


class EmailService:

    async def send_email(
        self,
        db: AsyncSession,
        notification: Notification,
        email: str
    ):

        

        await outbox_service.queue_event(
            db=db,
            topic="notification.email.send",
            payload={
                "notification_id": notification.id,
                "email": email,
                "subject": subject,
                "message": notification.message
            }
        )

        

        return notification


email_service = EmailService()