from sqlalchemy.orm import Session
from fastapi import HTTPException

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
    # RESERVE STOCK (CART / CHECKOUT PREP)
    # =====================================
    def reserve_stock(
        self,
        db: Session,
        inventory_id: str,
        quantity: int,
        user_id: str,
        ip: str
    ):

        inventory = (
            db.query(Inventory)
            .filter(Inventory.id == inventory_id)
            .with_for_update()
            .first()
        )

        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")

        self.validator.validate_stock(inventory=inventory, quantity=quantity)

        inventory.available_stock -= quantity
        inventory.reserved_stock += quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="reserve",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        db.commit()
        db.refresh(inventory)

        self._emit_inventory_event(
            event="inventory_reserved",
            inventory=inventory,
            quantity=quantity,
            user_id=user_id
        )

        self._audit(
            db, user_id, "inventory_reserved",
            inventory, quantity, ip
        )

        return inventory

    # =====================================
    # CONFIRM SALE (POST PAYMENT / ORDER FINALIZATION)
    # =====================================
    def confirm_sale(
        self,
        db: Session,
        inventory_id: str,
        quantity: int,
        user_id: str,
        ip: str
    ):

        inventory = (
            db.query(Inventory)
            .filter(Inventory.id == inventory_id)
            .with_for_update()
            .first()
        )

        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")

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
        db.commit()
        db.refresh(inventory)

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
    # RELEASE RESERVED STOCK (CANCELLED ORDER / FAILED PAYMENT)
    # =====================================
    def release_reserved_stock(
        self,
        db: Session,
        inventory_id: str,
        quantity: int,
        user_id: str,
        ip: str
    ):

        inventory = (
            db.query(Inventory)
            .filter(Inventory.id == inventory_id)
            .with_for_update()
            .first()
        )

        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")

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
        db.commit()
        db.refresh(inventory)

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
    # REDUCE STOCK (ADMIN / EMERGENCY ADJUSTMENT)
    # =====================================
    def reduce_stock(
        self,
        db: Session,
        inventory_id: str,
        quantity: int,
        user_id: str,
        ip: str
    ):

        inventory = (
            db.query(Inventory)
            .filter(Inventory.id == inventory_id)
            .with_for_update()
            .first()
        )

        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")

        self.validator.validate_stock(inventory=inventory, quantity=quantity)

        inventory.available_stock -= quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="manual_reduce",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        db.commit()
        db.refresh(inventory)

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
    # 🆕 CHECKOUT FINALIZATION (BUSHMARKET CORE EXTENSION)
    # THIS CONNECTS:
    # cart → payment → inventory → order system
    # =====================================
    def finalize_checkout(
        self,
        db: Session,
        inventory_id: str,
        quantity: int,
        user_id: str,
        ip: str,
        order_id: str
    ):

        inventory = (
            db.query(Inventory)
            .filter(Inventory.id == inventory_id)
            .with_for_update()
            .first()
        )

        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")

        if inventory.reserved_stock < quantity:
            raise HTTPException(status_code=400, detail="Reserved stock insufficient for checkout")

        # convert reserved → sold
        inventory.reserved_stock -= quantity
        inventory.sold_stock += quantity

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="checkout_finalized",
            quantity=quantity,
            created_by=user_id
        )

        db.add(tx)
        db.commit()
        db.refresh(inventory)

        self._emit_inventory_event(
            event="checkout_completed",
            inventory=inventory,
            quantity=quantity,
            user_id=user_id,
            extra={"order_id": order_id}
        )

        self._audit(
            db, user_id, "checkout_completed",
            inventory, quantity, ip
        )

        return inventory

    # =====================================
    # INTERNAL: EVENT EMITTER
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
    # INTERNAL: AUDIT LOGGER
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