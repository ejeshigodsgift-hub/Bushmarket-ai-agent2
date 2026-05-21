from models.delivery import Delivery, DeliveryStatus
from events.event_bus import EventBus
from events.event_types import DELIVERY_COMPLETED


class DeliveryService:

    def __init__(self):
        self.events = EventBus()

    def create_delivery(self, db, order, user_id):

        delivery = Delivery(
            order_id=order.id,
            cooperative_id=order.cooperative_id,
            user_id=user_id,
            status=DeliveryStatus.pending
        )

        db.add(delivery)
        db.commit()
        db.refresh(delivery)

        return delivery

    def mark_delivered(self, db, delivery):

        delivery.status = DeliveryStatus.delivered
        db.commit()

        self.events.publish(DELIVERY_COMPLETED, {
            "delivery_id": delivery.id,
            "order_id": delivery.order_id
        })

        return delivery