
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification

from app.services.notification_service import (
notification_service
)

class NotificationHandler:

async def handle(
    self,
    db: AsyncSession,
    event: dict
):

    topic = event["topic"]
    payload = event["payload"]

    # ===================================
    # SMS NOTIFICATION
    # ===================================
    if topic == "notification.sms.send":

        stmt = (
            select(Notification)
            .where(
                Notification.id ==
                payload["notification_id"]
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        notification = result.scalar_one_or_none()

        # ===================================
        # NOTIFICATION NOT FOUND
        # ===================================
        if not notification:
            return

        try:

            # ===================================
            # CALL SMS PROVIDER
            # Replace with actual provider
            # ===================================
            sms_sent = True

            if sms_sent:

                await notification_service.mark_delivered(
                    db=db,
                    notification=notification
                )

            else:

                await notification_service.mark_failed(
                    db=db,
                    notification=notification,
                    reason="SMS provider returned failure"
                )

            await db.commit()

        except Exception as exc:

            await notification_service.mark_failed(
                db=db,
                notification=notification,
                reason=str(exc)
            )

            await db.commit()

    # ===================================
    # EMAIL NOTIFICATION
    # ===================================
    elif topic == "notification.email.send":

        stmt = (
            select(Notification)
            .where(
                Notification.id ==
                payload["notification_id"]
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        notification = result.scalar_one_or_none()

        if not notification:
            return

        try:

            # ===================================
            # CALL EMAIL PROVIDER
            # ===================================
            email_sent = True

            if email_sent:

                await  notification_service.mark_sent(
                    db=db,
                 notification=notification
                )

            else:

                await notification_service.mark_failed(
                    db=db,
                    notification=notification,
                    reason="Email provider returned failure"
                )

            await db.commit()

        except Exception as exc:

            await notification_service.mark_failed(
                db=db,
                notification=notification,
                reason=str(exc)
            )

            await db.commit()

    # ===================================
    # PUSH NOTIFICATION
    # ===================================
    elif topic == "notification.push.send":

        stmt = (
            select(Notification)
            .where(
                Notification.id ==
                payload["notification_id"]
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        notification = result.scalar_one_or_none()

        if not notification:
            return

        try:

            # ===================================
            # CALL PUSH PROVIDER
            # ===================================
            push_sent = True

            if push_sent:

                await notification_service.mark_delivered(
                    db=db,
                    notification=notification
                )

            else:

                await notification_service.mark_failed(
                    db=db,
                    notification=notification,
                    reason="Push provider returned failure"
                )

            await db.commit()

        except Exception as exc:

            await notification_service.mark_failed(
                db=db,
                notification=notification,
                reason=str(exc)
            )

            await db.commit()

notification_handler = NotificationHandler()