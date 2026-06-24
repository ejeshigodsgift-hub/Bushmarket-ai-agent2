from datetime import datetime, timezone

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

    # =========================================
    # CREATE NOTIFICATION
    # =========================================
    async def create_notification(
        self,
        db: AsyncSession,
        user_id: str,
        channel: str,
        title: str,
        message: str
    ) -> Notification:

        notification = Notification(
            user_id=user_id,
            channel=channel,
            title=title,
            message=message,
            status="pending"
        )

        db.add(notification)

        await db.flush()

        return notification

    # =========================================
    # SEND EMAIL
    # =========================================
    async def send_email(
        self,
        db: AsyncSession,
        user_id: str,
        email: str,
        subject: str,
        message: str
    ) -> Notification:

        notification = await self.create_notification(
            db=db,
            user_id=user_id,
            channel="email",
            title=subject,
            message=message
        )

        await email_service.send_email(
            db=db,
            notification=notification,
            email=email
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="notification_email_sent",
            entity_type="notification",
            entity_id=notification.id
        )

        return notification

    # =========================================
    # SEND SMS
    # =========================================
    async def send_sms(
        self,
        db: AsyncSession,
        user_id: str,
        phone_number: str,
        message: str
    ) -> Notification:

        notification = await self.create_notification(
            db=db,
            user_id=user_id,
            channel="sms",
            title="SMS Notification",
            message=message
        )

        await sms_service.send_sms(
            db=db,
            notification=notification,
            phone_number=phone_number
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="notification_sms_sent",
            entity_type="notification",
            entity_id=notification.id
        )

        return notification

    # =========================================
    # SEND PUSH
    # =========================================
    async def send_push(
        self,
        db: AsyncSession,
        user_id: str,
        device_token: str,
        title: str,
        message: str
    ) -> Notification:

        notification = await self.create_notification(
            db=db,
            user_id=user_id,
            channel="push",
            title=title,
            message=message
        )

        await push_service.send_push(
            db=db,
            notification=notification,
            device_token=device_token
        )

        await self.audit.log(
            db=db,
            user_id=user_id,
            action="notification_push_sent",
            entity_type="notification",
            entity_id=notification.id
        )

        return notification

    # =========================================
    # MARK DELIVERED
    # =========================================
    async def mark_delivered(
        self,
        db: AsyncSession,
        notification: Notification
    ) -> Notification:

        notification.status = "delivered"

        notification.sent_at = datetime.now(
            timezone.utc
        )

        await db.flush()

        await outbox_service.queue_event(
            db=db,
            topic="notification.delivered",
            payload={
                "notification_id": notification.id
            }
        )

        return notification

    # =========================================
    # MARK FAILED
    # =========================================
    async def mark_failed(
        self,
        db: AsyncSession,
        notification: Notification,
        reason: str
    ) -> Notification:

        notification.status = "failed"

        await db.flush()

        await outbox_service.queue_event(
            db=db,
            topic="notification.failed",
            payload={
                "notification_id": notification.id,
                "reason": reason
            }
        )

        return notification

    # =========================================
    # MARK READ
    # =========================================
    async def mark_read(
        self,
        db: AsyncSession,
        notification: Notification
    ) -> Notification:

        notification.is_read = True

        await db.flush()

        return notification


notification_service = NotificationService()