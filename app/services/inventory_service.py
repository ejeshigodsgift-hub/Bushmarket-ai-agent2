from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta

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
    def get_inventory(self, db: Session, inventory_id: str):

        inventory = (
            db.query(Inventory)
            .filter(Inventory.id == inventory_id)
            .first()
        )

        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")

        return inventory

    # =====================================
    # RESERVE STOCK (WITH TTL)
    # =====================================
    def reserve_stock(
        self,
        db: Session,
        inventory: Inventory,
        quantity: int,
        user_id: str,
        ip: str = None
    ):

        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")

        self.validator.validate_stock(
            inventory=inventory,
            quantity=quantity
        )

        now = datetime.utcnow()

        # TTL reservation fields (NEW LOGIC)
        inventory.reserved_at = now
        inventory.expires_at = now + timedelta(minutes=5)

        # lock-safe update
        inventory.available_stock -= quantity
        inventory.reserved_stock += quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="reserve",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        db.flush()

        self._emit_inventory_event(
            event="inventory_reserved",
            inventory=inventory,
            quantity=quantity,
            user_id=user_id
        )

        self._audit(
            db=db,
            user_id=user_id,
            action="inventory_reserved",
            inventory=inventory,
            quantity=quantity,
            ip=ip
        )

        return inventory

    # =====================================
    # CONFIRM SALE
    # =====================================
    def confirm_sale(
        self,
        db: Session,
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
        db.flush()

        self._emit_inventory_event(
            event="inventory_sold",
            inventory=inventory,
            quantity=quantity,
            user_id=user_id
        )

        self._audit(
            db, user_id, "inventory_sold",
            inventory, quantity, ip
        )

        return inventory

    # =====================================
    # RELEASE RESERVED STOCK
    # =====================================
    def release_reserved_stock(
        self,
        db: Session,
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
        db.flush()

        self._emit_inventory_event(
            event="inventory_released",
            inventory=inventory,
            quantity=quantity,
            user_id=user_id
        )

        self._audit(
            db, user_id, "inventory_released",
            inventory, quantity, ip
        )

        return inventory

    # =====================================
    # REDUCE STOCK
    # =====================================
    def reduce_stock(
        self,
        db: Session,
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
        db.flush()

        self._emit_inventory_event(
            event="inventory_reduced",
            inventory=inventory,
            quantity=quantity,
            user_id=user_id
        )

        self._audit(
            db, user_id, "inventory_reduced",
            inventory, quantity, ip
        )

        return inventory

    # =====================================
    # FINALIZE CHECKOUT
    # =====================================
    def finalize_checkout(
        self,
        db: Session,
        inventory: Inventory,
        quantity: int,
        user_id: str,
        ip: str,
        order_id: str
    ):

        if inventory.reserved_stock < quantity:
            raise HTTPException(
                status_code=400,
                detail="Reserved stock insufficient for checkout"
            )

        inventory.reserved_stock -= quantity
        inventory.sold_stock += quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="checkout_finalized",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        db.flush()

        self._emit_inventory_event(
            event="checkout_completed",
            inventory=inventory,
            quantity=quantity,
            user_id=user_id,
            extra={"order_id": order_id}
        )

        self._audit(
            db, user_id,
            "checkout_completed",
            inventory,
            quantity,
            ip
        )

        return inventory

    # =====================================
    # EVENT EMITTER
    # =====================================
    def _emit_inventory_event(self, event, inventory, quantity, user_id, extra=None):

        payload = {
            "event": event,
            "inventory_id": inventory.id,
            "quantity": quantity,
            "user_id": user_id,
            "available_stock": inventory.available_stock,
            "reserved_stock": inventory.reserved_stock,
            "sold_stock": inventory.sold_stock,
            "extra": extra or {}
        }

        redis_client.publish("inventory.updated", payload)
        event_bus.publish("inventory-events", payload)

    # =====================================
    # AUDIT
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
                "sold_stock": inventory.sold_stock
            },
            ip=ip
        )