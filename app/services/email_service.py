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
        user_id: str,
        email: str,
        subject: str,
        message: str
    ):

        notification = Notification(
            user_id=user_id,
            channel="email",
            title=subject,
            message=message,
            status="pending"
        )

        db.add(notification)
       
        await db.flush()

        await outbox_service.queue_event(
            db=db,
            topic="notification.email.send",
            payload={
                "notification_id": notification.id,
                "email": email,
                "subject": subject,
                "message": message
            }
        )

        notification.status = "pending"
        notification.sent_at = datetime.now(timezone.utc)

        return notification


email_service = EmailService()