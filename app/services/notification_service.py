from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification

from app.services.email_service import email_service
from app.services.sms_service import sms_service
from app.services.push_service import push_service

from app.services.audit_service import AuditService
from app.services.outbox_service import outbox_service


class NotificationService:

    def __init__(self):
        self.audit = AuditService()

    async def create_notification(
        self,
        db: AsyncSession,
        user_id: str,
        channel: str,
        title: str,
        message: str
    ):

        notification = Notification(
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            status="pending"
        )

        db.add(notification)

        return notification

    async def send_email(
        self,
        db: AsyncSession,
        user_id: str,
        email: str,
        subject: str,
        message: str
    ):

        notification = await email_service.send_email(
            db=db,
            user_id=user_id,
            email=email,
            subject=subject,
            message=message
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="notification_email_sent",
            entity_type="notification",
            entity_id=notification.id
        )

        return notification

    async def send_sms(
        self,
        db: AsyncSession,
        user_id: str,
        phone_number: str,
        message: str
    ):

        notification = await sms_service.send_sms(
            db=db,
            user_id=user_id,
            phone_number=phone_number,
            message=message
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="notification_sms_sent",
            entity_type="notification",
            entity_id=notification.id
        )

        return notification

    async def send_push(
        self,
        db: AsyncSession,
        user_id: str,
        device_token: str,
        title: str,
        message: str
    ):

        notification = await push_service.send_push(
            db=db,
            user_id=user_id,
            device_token=device_token,
            title=title,
            message=message
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="notification_push_sent",
            entity_type="notification",
            entity_id=notification.id
        )

        return notification

    async def mark_delivered(
        self,
        db: AsyncSession,
        notification: Notification
    ):

        notification.status = "delivered"

        await outbox_service.queue_event(
            db=db,
            topic="notification.delivered",
            payload={
                "notification_id": notification.id
            }
        )

        return notification

    async def mark_failed(
        self,
        db: AsyncSession,
        notification: Notification,
        reason: str
    ):

        notification.status = "failed"

        await outbox_service.queue_event(
            db=db,
            topic="notification.failed",
            payload={
                "notification_id": notification.id,
                "reason": reason
            }
        )

        return notification

    async def mark_read(
        self,
        notification: Notification
    ):

        notification.is_read = True

        return notification


notification_service = NotificationService()