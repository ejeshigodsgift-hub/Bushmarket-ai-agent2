from datetime import datetime, timezone

from sqlalchemy import select

from app.db.models.notification import Notification


class NotificationHandler:

    async def handle(
        self,
        db,
        event
    ):

        topic = event["topic"]
        payload = event["payload"]

        if topic == "notification.sms.send":

            # ===================================
            # CALL SMS PROVIDER
            # ===================================
            sms_sent = True

            # ===================================
            # SMS SENT SUCCESSFULLY
            # ===================================
            if sms_sent:

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

                if notification:

                    notification.status = "sent"

                    notification.sent_at = (
                        datetime.now(timezone.utc)
                    )

                    await db.commit()