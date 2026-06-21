from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.inventory import Inventory
from app.db.models.inventory_transaction import InventoryTransaction

from app.services.inventory_validation_service import InventoryValidationService
from app.services.audit_service import AuditService

from app.integrations.redis_client import redis_client
from app.integrations.kafka_client import event_bus


class InventoryService:

    def __init__(self):
        self.validator = InventoryValidationService()
        self.audit = AuditService()

    # =====================================
    # GET INVENTORY
    # =====================================
    async def get_inventory(self, db: AsyncSession, inventory_id: str):

        result = await db.execute(
            select(Inventory).where(Inventory.id == inventory_id)
        )
        inventory = result.scalar_one_or_none()

        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")

        return inventory

    # =====================================
    # RESERVE STOCK
    # =====================================
    async def reserve_stock(
        self,
        db: AsyncSession,
        inventory: Inventory,
        quantity: int,
        user_id: str,
        ip: str = None
    ):

        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")

        self.validator.validate_stock(inventory, quantity)

        now = datetime.utcnow()

        inventory.reserved_at = now
        inventory.expires_at = now + timedelta(minutes=5)

        inventory.available_stock -= quantity
        inventory.reserved_stock += quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="reserve",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        await db.flush()

        self._emit_inventory_event(
            "inventory_reserved",
            inventory,
            quantity,
            user_id
        )

        self._audit(db, user_id, "inventory_reserved", inventory, quantity, ip)

        return inventory

    # =====================================
    # CONVERT RESERVATION → CHECKOUT
    # =====================================
    async def convert_reservation_to_checkout(
        self,
        db: AsyncSession,
        listing_id: str,
        quantity: int,
        user_id: str,
        ip: str = None
    ):

        result = await db.execute(
            select(Inventory).where(
                Inventory.listing_id == listing_id,
                Inventory.is_active == True
            ).with_for_update()
        )
        inventory = result.scalar_one_or_none()

        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")

        if inventory.reserved_stock < quantity:
            raise HTTPException(status_code=400, detail="Reserved inventory mismatch")

        if inventory.checkout_reserved_quantity is None:
            inventory.checkout_reserved_quantity = 0

        inventory.checkout_reserved_quantity += quantity
        inventory.reserved_stock -= quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="checkout_reserved",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        await db.flush()

        self._emit_inventory_event(
            "inventory_checkout_reserved",
            inventory,
            quantity,
            user_id
        )

        self._audit(db, user_id, "inventory_checkout_reserved", inventory, quantity, ip)

        return inventory

    # =====================================
    # CONFIRM SALE
    # =====================================
    async def confirm_sale(
        self,
        db: AsyncSession,
        inventory: Inventory,
        quantity: int,
        user_id: str,
        ip: str = None
    ):

        if inventory.reserved_stock < quantity:
            raise HTTPException(status_code=400, detail="Reserved stock insufficient")

        inventory.reserved_stock -= quantity
        inventory.sold_stock += quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="sold",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        await db.flush()

        self._emit_inventory_event(
            "inventory_sold",
            inventory,
            quantity,
            user_id
        )

        self._audit(db, user_id, "inventory_sold", inventory, quantity, ip)

        return inventory

    # =====================================
    # RELEASE RESERVED STOCK
    # =====================================
    async def release_reserved_stock(
        self,
        db: AsyncSession,
        inventory: Inventory,
        quantity: int,
        user_id: str,
        ip: str = None
    ):

        if inventory.reserved_stock < quantity:
            raise HTTPException(status_code=400, detail="Reserved stock insufficient")

        inventory.reserved_stock -= quantity
        inventory.available_stock += quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="release",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        await db.flush()

        self._emit_inventory_event(
            "inventory_released",
            inventory,
            quantity,
            user_id
        )

        self._audit(db, user_id, "inventory_released", inventory, quantity, ip)

        return inventory

    # =====================================
    # CANCEL RESERVATION (ASYNC FIXED)
    # =====================================
    async def cancel_reservation(
        self,
        db: AsyncSession,
        inventory: Inventory,
        quantity: int,
        user_id: str,
        reason: str = "expiry",
        ip: str = None
    ):

        if inventory.reserved_stock < quantity:
            raise HTTPException(
                status_code=400,
                detail="Reserved stock insufficient for cancellation"
            )

        inventory.reserved_stock -= quantity
        inventory.available_stock += quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="cancelled_reservation",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        await db.flush()

        self._emit_inventory_event(
            "inventory_reservation_cancelled",
            inventory,
            quantity,
            user_id,
            extra={"reason": reason}
        )

        self._audit(
            db,
            user_id,
            "inventory_reservation_cancelled",
            inventory,
            quantity,
            ip
        )

        return inventory

    # =====================================
    # REDUCE STOCK
    # =====================================
    async def reduce_stock(
        self,
        db: AsyncSession,
        inventory: Inventory,
        quantity: int,
        user_id: str,
        ip: str = None
    ):

        self.validator.validate_stock(inventory, quantity)

        inventory.available_stock -= quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="manual_reduce",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        await db.flush()

        self._emit_inventory_event(
            "inventory_reduced",
            inventory,
            quantity,
            user_id
        )

        self._audit(db, user_id, "inventory_reduced", inventory, quantity, ip)

        return inventory

    # =====================================
    # FINALIZE CHECKOUT
    # =====================================
    async def finalize_checkout(
        self,
        db: AsyncSession,
        inventory: Inventory,
        quantity: int,
        user_id: str,
        ip: str,
        order_id: str
    ):

        if inventory.checkout_reserved_quantity is None:
            inventory.checkout_reserved_quantity = 0

        if inventory.checkout_reserved_quantity < quantity:
            raise HTTPException(
                status_code=400,
                detail="Checkout reserved stock insufficient for finalization"
            )

        inventory.checkout_reserved_quantity -= quantity
        inventory.sold_stock += quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="checkout_finalized",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        await db.flush()

        self._emit_inventory_event(
            "checkout_completed",
            inventory,
            quantity,
            user_id,
            extra={"order_id": order_id}
        )

        self._audit(db, user_id, "checkout_completed", inventory, quantity, ip)

        return inventory

    # =====================================
    # EVENT EMITTER (UNCHANGED)
    # =====================================
    def _emit_inventory_event(self, event, inventory, quantity, user_id, extra=None):

        payload = {
            "event": event,
            "inventory_id": inventory.id,
            "quantity": quantity,
            "user_id": user_id,
            "available_stock": inventory.available_stock,
            "reserved_stock": inventory.reserved_stock,
            "checkout_reserved_quantity": getattr(inventory, "checkout_reserved_quantity", 0),
            "sold_stock": inventory.sold_stock,
            "extra": extra or {}
        }

        redis_client.publish("inventory.updated", payload)
        event_bus.publish("inventory-events", payload)

    # =====================================
    # AUDIT (UNCHANGED SYNC CALL)
    # =====================================
    def _audit(self, db, user_id, action, inventory, quantity, ip):

        self.audit.log(
            db=db,
            user_id=user_id,
            action=action,
            entity_type="inventory",
            entity_id=inventory.id,
            metadata={
                "quantity": quantity,
                "available_stock": inventory.available_stock,
                "reserved_stock": inventory.reserved_stock,
                "checkout_reserved_quantity": getattr(inventory, "checkout_reserved_quantity", 0),
                "sold_stock": inventory.sold_stock
            },
            ip=ip
        )