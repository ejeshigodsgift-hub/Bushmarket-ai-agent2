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
    # RESERVE STOCK
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
        db.flush()

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
    def convert_reservation_to_checkout(
        self,
        db: Session,
        listing_id: str,
        quantity: int,
        user_id: str,
        ip: str = None
    ):

        inventory = (
            db.query(Inventory)
            .filter(
                Inventory.listing_id == listing_id,
                Inventory.is_active == True
            )
            .with_for_update()
            .first()
        )

        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")

        if inventory.reserved_stock < quantity:
            raise HTTPException(
                status_code=400,
                detail="Reserved inventory mismatch"
            )

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
        db.flush()

        self._emit_inventory_event(
            "inventory_checkout_reserved",
            inventory,
            quantity,
            user_id
        )

        self._audit(
            db,
            user_id,
            "inventory_checkout_reserved",
            inventory,
            quantity,
            ip
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
            "inventory_released",
            inventory,
            quantity,
            user_id
        )

        self._audit(db, user_id, "inventory_released", inventory, quantity, ip)

        return inventory

    

    def cancel_reservation(
        self,
        db: Session,
        inventory: Inventory,
        quantity: int,
        user_id: str,
        reason: str = "expiry",
        ip: str = None
    ):
        """
        Releases reserved stock when:
        - checkout expires
        - order is cancelled
        """

        if inventory.reserved_stock < quantity:
            raise HTTPException(
                status_code=400,
                detail="Reserved stock  insufficient for cancellation"
            )

        # RETURN STOCK BACK
        inventory.reserved_stock -= quantity
        inventory.available_stock += quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
        transaction_type="cancelled_reservation",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        db.flush()

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
            "inventory_reduced",
            inventory,
            quantity,
            user_id
        )

        self._audit(db, user_id, "inventory_reduced", inventory, quantity, ip)

        return inventory

    # =====================================
    # FINALIZE CHECKOUT (FIXED)
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

        # ✅ FIX: use checkout_reserved_quantity (NOT reserved_stock)
        if inventory.checkout_reserved_quantity is None:
            inventory.checkout_reserved_quantity = 0

        if inventory.checkout_reserved_quantity < quantity:
            raise HTTPException(
                status_code=400,
                detail="Checkout reserved stock insufficient for finalization"
            )

        # FINAL SALE LOGIC
        inventory.checkout_reserved_quantity -= quantity
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
            "checkout_completed",
            inventory,
            quantity,
            user_id,
            extra={"order_id": order_id}
        )

        self._audit(
            db,
            user_id,
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
            "checkout_reserved_quantity": getattr(inventory, "checkout_reserved_quantity", 0),
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
                "checkout_reserved_quantity": getattr(inventory, "checkout_reserved_quantity", 0),
                "sold_stock": inventory.sold_stock
            },
            ip=ip
        )