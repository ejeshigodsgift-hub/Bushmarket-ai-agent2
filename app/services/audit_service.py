# =====================================
# FILE: app/services/audit_service.py
# =====================================

from datetime import # =====================================
# FILE: app/services/audit_service.py
# =====================================

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.integrations.redis_client import redis_client
from app.services.outbox_service import outbox_service


class AuditService:

    # =====================================
    # CORE LOG METHOD
    # =====================================
    async def log(
        self,
        db: AsyncSession,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str | None,
        metadata: dict,
        ip: str | None = None,
        session_id: str | None = None,
        device_id: str | None = None
    ):

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            event_data=metadata,
            ip_address=ip,
            session_id=session_id,
            device_id=device_id,
            created_at=datetime.now(timezone.utc)
        )

        db.add(audit_log)
        await db.flush()

        # =====================================
        # REDIS STREAM (REAL-TIME)
        # =====================================
        await redis_client.publish(
            "audit.events",
            {
                "audit_id": audit_log.id,
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "session_id": session_id,
                "device_id": device_id
            }
        )

        # =====================================
        # OUTBOX EVENT (RELIABLE DELIVERY)
        # =====================================
        await outbox_service.queue_event(
            db=db,
            topic="audit.log.created",
            payload={
                "audit_id": audit_log.id,
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "session_id": session_id,
                "device_id": device_id
            }
        )

        await db.flush()

        return audit_log


    # =====================================
    # ORDER EVENTS
    # =====================================
    async def log_order_created(
        self,
        db: AsyncSession,
        user_id: str,
        order_id: str,
        total_amount: float,
        ip: str | None = None
    ):
        return await self.log(
            db=db,
            user_id=user_id,
            action="order_created",
            entity_type="order",
            entity_id=order_id,
            metadata={"total_amount": total_amount},
            ip=ip
        )


    async def log_checkout_completed(
        self,
        db: AsyncSession,
        user_id: str,
        order_id: str,
        cart_id: str,
        ip: str | None = None
    ):
        return await self.log(
            db=db,
            user_id=user_id,
            action="checkout_completed",
            entity_type="cart",
            entity_id=cart_id,
            metadata={"order_id": order_id},
            ip=ip
        )


    async def log_payment_completed(
        self,
        db: AsyncSession,
        user_id: str,
        order_id: str,
        payment_reference: str,
        ip: str | None = None
    ):
        return await self.log(
            db=db,
            user_id=user_id,
            action="payment_completed",
            entity_type="payment",
            entity_id=order_id,
            metadata={"payment_reference": payment_reference},
            ip=ip
        )


    # =====================================
    # INVENTORY EVENTS
    # =====================================
    async def log_inventory_reserved(
        self,
        db: AsyncSession,
        user_id: str,
        inventory_id: str,
        quantity: int,
        ip: str | None = None
    ):
        return await self.log(
            db=db,
            user_id=user_id,
            action="inventory_reserved",
            entity_type="inventory",
            entity_id=inventory_id,
            metadata={"quantity": quantity},
            ip=ip
        )


    async def log_inventory_sold(
        self,
        db: AsyncSession,
        user_id: str,
        inventory_id: str,
        quantity: int,
        ip: str | None = None
    ):
        return await self.log(
            db=db,
            user_id=user_id,
            action="inventory_sold",
            entity_type="inventory",
            entity_id=inventory_id,
            metadata={"quantity": quantity},
            ip=ip
        )


    async def log_inventory_released(
        self,
        db: AsyncSession,
        user_id: str,
        inventory_id: str,
        quantity: int,
        ip: str | None = None
    ):
        return await self.log(
            db=db,
            user_id=user_id,
            action="inventory_released",
            entity_type="inventory",
            entity_id=inventory_id,
            metadata={"quantity": quantity},
            ip=ip
        )


audit_service = AuditService(), timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog

from app.integrations.redis_client import redis_client

from app.services.outbox_service import outbox_service




class AuditService:

    async def log(
        self,
        db: AsyncSession,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str | None,
        metadata: dict,
        ip: str | None = None,
        session_id: str | None = None,
        device_id: str | None = None
    ):

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            event_data=metadata,
            ip_address=ip,
            session_id=session_id,
            device_id=device_id,
            created_at=datetime.now(timezone.utc)
        )

        db.add(audit_log)
        await db.flush()

        # =====================================
        # REDIS STREAM (REAL-TIME EVENT)
        # =====================================
        await redis_client.publish(
            "audit.events",
            {
                "audit_id": audit_log.id,
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id
            }
        )

        # =====================================
        # OUTBOX (RELIABLE EVENT DELIVERY)
        # =====================================
        await outbox_service.queue_event(
            db=db,
            topic="audit.log.created",
            payload={
                "audit_id": audit_log.id,
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id
            }
        )

        await db.flush()  # IMPORTANT: no commit here

        return audit_log





    # =====================================
    # MARKETPLACE ORDER EVENTS
    # =====================================

    async def log_order_created(
        self,
        db: AsyncSession,
        user_id: str,
        order_id: str,
        total_amount: float,
        ip: str | None = None
    ):

        return await self.log(
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

    async def log_checkout_completed(
        self,
        db: AsyncSession,
        user_id: str,
        order_id: str,
        cart_id: str,
        ip: str | None = None
    ):

        return await self.log(
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

    async def log_payment_completed(
        self,
        db: AsyncSession,
        user_id: str,
        order_id: str,
        payment_reference: str,
        ip: str | None = None
    ):

        return await self.log(
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

    async def log_inventory_reserved(
        self,
        db: AsyncSession,
        user_id: str,
        inventory_id: str,
        quantity: int,
        ip: str | None = None
    ):

        return await self.log(
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

    async def log_inventory_sold(
        self,
        db: AsyncSession,
        user_id: str,
        inventory_id: str,
        quantity: int,
        ip: str | None = None
    ):

        return await self.log(
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

    async def log_inventory_released(
        self,
        db: AsyncSession,
        user_id: str,
        inventory_id: str,
        quantity: int,
        ip: str | None = None
    ):

        return await self.log(
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