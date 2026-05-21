from models.notification import Notification, NotificationType
from services.ai_notification_engine import AINotificationEngine


class NotificationService:

    def __init__(self):
        self.ai_engine = AINotificationEngine()

    # -----------------------------
    # CREATE NOTIFICATION
    # -----------------------------
    def create_notification(self, db, user_id: int, title: str, message: str, coop_id=None):

        notification = Notification(
            user_id=user_id,
            cooperative_id=coop_id,
            title=title,
            message=message,
            type=NotificationType.info
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    # -----------------------------
    # EVENT-DRIVEN HANDLER
    # -----------------------------
    def handle_event(self, db, event_type: str, payload: dict):

        coop_id = payload.get("cooperative_id")
        user_ids = payload.get("user_ids", [])

        # AI message generation
        ai_message = self.ai_engine.generate_message(event_type, payload)

        notifications = []

        for user_id in user_ids:
            notif = Notification(
                user_id=user_id,
                cooperative_id=coop_id,
                title="Bushmarket Update",
                message=ai_message,
                type=NotificationType.ai
            )

            db.add(notif)
            notifications.append(notif)

        db.commit()

        return notifications