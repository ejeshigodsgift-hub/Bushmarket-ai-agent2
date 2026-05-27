from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from app.db.models.audit_log import AuditLog

from app.integrations.kafka_client import event_bus
from app.integrations.redis_client import redis_client


class AuditService:

    # =====================================
    # CREATE AUDIT LOG
    # =====================================
    def log(
        self,
        db: DBSession,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str | None,
        metadata: dict,
        ip: str | None = None,
        session_id: str | None = None,
        device_id: str | None = None
    ):

        log = AuditLog(

            user_id=user_id,

            action=action,

            entity_type=entity_type,

            entity_id=entity_id,

            # CONSISTENT NAMING
            event_data=metadata,

            ip_address=ip,

            session_id=session_id,

            device_id=device_id,

            created_at=datetime.now(timezone.utc)
        )

        db.add(log)
        db.commit()
        db.refresh(log)

        # =====================================
        # REDIS AUDIT STREAM CACHE
        # =====================================

        redis_client.publish(
            "audit.events",
            {
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id
            }
        )

        # =====================================
        # KAFKA EVENT BUS
        # =====================================

        event_bus.publish(
            "audit.log.created",
            {
                "audit_id": log.id,
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id
            }
        )

        return log

    # =====================================
    # MARKETPLACE ORDER EVENTS
    # =====================================

    def log_order_created(
        self,
        db: DBSession,
        user_id: str,
        order_id: str,
        total_amount: float,
        ip: str | None = None
    ):

        return self.log(
            db=db,
            user_id=user_id,
            action="order_created",
            entity_type="order",
            entity_id=order_id,
            metadata={
                "total_amount": total_amount
            },
            ip=ip
        )

    def log_checkout_completed(
        self,
        db: DBSession,
        user_id: str,
        order_id: str,
        cart_id: str,
        ip: str | None = None
    ):

        return self.log(
            db=db,
            user_id=user_id,
            action="checkout_completed",
            entity_type="cart",
            entity_id=cart_id,
            metadata={
                "order_id": order_id
            },
            ip=ip
        )

    def log_payment_completed(
        self,
        db: DBSession,
        user_id: str,
        order_id: str,
        payment_reference: str,
        ip: str | None = None
    ):

        return self.log(
            db=db,
            user_id=user_id,
            action="payment_completed",
            entity_type="payment",
            entity_id=order_id,
            metadata={
                "payment_reference": payment_reference
            },
            ip=ip
        )

    # =====================================
    # INVENTORY EVENTS
    # =====================================

    def log_inventory_reserved(
        self,
        db: DBSession,
        user_id: str,
        inventory_id: str,
        quantity: int,
        ip: str | None = None
    ):

        return self.log(
            db=db,
            user_id=user_id,
            action="inventory_reserved",
            entity_type="inventory",
            entity_id=inventory_id,
            metadata={
                "quantity": quantity
            },
            ip=ip
        )

    def log_inventory_sold(
        self,
        db: DBSession,
        user_id: str,
        inventory_id: str,
        quantity: int,
        ip: str | None = None
    ):

        return self.log(
            db=db,
            user_id=user_id,
            action="inventory_sold",
            entity_type="inventory",
            entity_id=inventory_id,
            metadata={
                "quantity": quantity
            },
            ip=ip
        )

    def log_inventory_released(
        self,
        db: DBSession,
        user_id: str,
        inventory_id: str,
        quantity: int,
        ip: str | None = None
    ):

        return self.log(
            db=db,
            user_id=user_id,
            action="inventory_released",
            entity_type="inventory",
            entity_id=inventory_id,
            metadata={
                "quantity": quantity
            },
            ip=ip
        )


audit_service = AuditService()