from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.integrations.redis_client import redis_client
from app.services.outbox_service import outbox_service
from app.services.audit_hash_service import generate_event_hash


class AuditService:

    # =====================================
    # CORE LOG METHOD (WITH EVENT HASH)
    # =====================================
    async def log(
        self,
        db: AsyncSession,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str | None,
        metadata: dict,
        reference: str | None = None,
        amount: float | None = None,
        ip: str | None = None,
        session_id: str | None = None,
        device_id: str | None = None
    ):

        timestamp = datetime.now(timezone.utc)

        # =====================================================
        # EVENT HASH (AUDIT INTEGRITY LAYER)
        # =====================================================
        event_hash = None

        if reference and amount is not None:
            event_hash = generate_event_hash(
                reference=reference,
                amount=str(amount),
                timestamp=str(timestamp)
            )

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            event_data=metadata,
            event_hash=event_hash,
            ip_address=ip,
            session_id=session_id,
            device_id=device_id,
            created_at=timestamp
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
                "entity_id": entity_id,
                "event_hash": event_hash
            }
        )

        # =====================================
        # OUTBOX (RELIABLE DELIVERY)
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
                "event_hash": event_hash
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
            reference=order_id,
            amount=total_amount,
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
            reference=order_id,
            ip=ip
        )

    async def log_payment_completed(
        self,
        db: AsyncSession,
        user_id: str,
        order_id: str,
        payment_reference: str,
        amount: float,
        ip: str | None = None
    ):
        return await self.log(
            db=db,
            user_id=user_id,
            action="payment_completed",
            entity_type="payment",
            entity_id=order_id,
            metadata={"payment_reference": payment_reference},
            reference=payment_reference,
            amount=amount,
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
            reference=inventory_id,
            amount=quantity,
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
            reference=inventory_id,
            amount=quantity,
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
            reference=inventory_id,
            amount=quantity,
            ip=ip
        )


audit_service = AuditService()