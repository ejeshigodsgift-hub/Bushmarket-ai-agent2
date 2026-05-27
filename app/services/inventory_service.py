from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models.inventory import Inventory
from app.db.models.inventory_transaction import (
    InventoryTransaction
)

from app.services.inventory_validation_service import (
    InventoryValidationService
)

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
    def get_inventory(
        self,
        db: Session,
        inventory_id: str
    ):

        inventory = (
            db.query(Inventory)
            .filter(Inventory.id == inventory_id)
            .first()
        )

        if not inventory:
            raise HTTPException(
                status_code=404,
                detail="Inventory not found"
            )

        return inventory

    # =====================================
    # RESERVE STOCK
    # Used During:
    # cart reservation
    # checkout preparation
    # cooperative reservation
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
            .filter(
                Inventory.id == inventory_id
            )
            .with_for_update()
            .first()
        )

        self.validator.validate_stock(
            inventory=inventory,
            quantity=quantity
        )

        inventory.available_stock -= quantity
        inventory.reserved_stock += quantity

        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="reserve",
            quantity=quantity,
            created_by=user_id
        )

        db.add(transaction)

        db.commit()
        db.refresh(inventory)

        # REDIS CACHE UPDATE
        redis_client.publish(
            "inventory.updated",
            {
                "inventory_id": inventory.id,
                "available_stock": inventory.available_stock,
                "reserved_stock": inventory.reserved_stock
            }
        )

        # KAFKA EVENT
        event_bus.publish(
            "inventory-events",
            {
                "event": "inventory_reserved",
                "inventory_id": inventory.id,
                "quantity": quantity,
                "user_id": user_id
            }
        )

        # AUDIT LOG
        self.audit.log(
            db=db,
            user_id=user_id,
            action="inventory_reserved",
            entity_type="inventory",
            entity_id=inventory.id,
            metadata={
                "quantity": quantity,
                "available_stock": inventory.available_stock
            },
            ip=ip
        )

        return inventory

    # =====================================
    # CONFIRM SALE
    # Used After:
    # successful payment
    # marketplace order creation
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
            .filter(
                Inventory.id == inventory_id
            )
            .with_for_update()
            .first()
        )

        if not inventory:
            raise HTTPException(
                status_code=404,
                detail="Inventory not found"
            )

        if inventory.reserved_stock < quantity:
            raise HTTPException(
                status_code=400,
                detail="Reserved stock insufficient"
            )

        inventory.reserved_stock -= quantity
        inventory.sold_stock += quantity

        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="sold",
            quantity=quantity,
            created_by=user_id
        )

        db.add(transaction)

        db.commit()
        db.refresh(inventory)

        # REDIS CACHE UPDATE
        redis_client.publish(
            "inventory.updated",
            {
                "inventory_id": inventory.id,
                "sold_stock": inventory.sold_stock
            }
        )

        # KAFKA EVENT
        event_bus.publish(
            "inventory-events",
            {
                "event": "inventory_sold",
                "inventory_id": inventory.id,
                "quantity": quantity,
                "user_id": user_id
            }
        )

        # AUDIT LOG
        self.audit.log(
            db=db,
            user_id=user_id,
            action="inventory_sold",
            entity_type="inventory",
            entity_id=inventory.id,
            metadata={
                "quantity": quantity,
                "sold_stock": inventory.sold_stock
            },
            ip=ip
        )

        return inventory

    # =====================================
    # RELEASE RESERVED STOCK
    # Used During:
    # cart expiration
    # failed payment
    # order cancellation
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
            .filter(
                Inventory.id == inventory_id
            )
            .with_for_update()
            .first()
        )

        if not inventory:
            raise HTTPException(
                status_code=404,
                detail="Inventory not found"
            )

        if inventory.reserved_stock < quantity:
            raise HTTPException(
                status_code=400,
                detail="Reserved stock insufficient"
            )

        inventory.reserved_stock -= quantity
        inventory.available_stock += quantity

        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="release",
            quantity=quantity,
            created_by=user_id
        )

        db.add(transaction)

        db.commit()
        db.refresh(inventory)

        # REDIS CACHE UPDATE
        redis_client.publish(
            "inventory.updated",
            {
                "inventory_id": inventory.id,
                "available_stock": inventory.available_stock,
                "reserved_stock": inventory.reserved_stock
            }
        )

        # KAFKA EVENT
        event_bus.publish(
            "inventory-events",
            {
                "event": "inventory_released",
                "inventory_id": inventory.id,
                "quantity": quantity,
                "user_id": user_id
            }
        )

        # AUDIT LOG
        self.audit.log(
            db=db,
            user_id=user_id,
            action="inventory_released",
            entity_type="inventory",
            entity_id=inventory.id,
            metadata={
                "quantity": quantity,
                "available_stock": inventory.available_stock
            },
            ip=ip
        )

        return inventory

    # =====================================
    # DIRECT STOCK REDUCTION
    # Used For:
    # admin corrections
    # emergency reconciliation
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
            .filter(
                Inventory.id == inventory_id
            )
            .with_for_update()
            .first()
        )

        self.validator.validate_stock(
            inventory=inventory,
            quantity=quantity
        )

        inventory.available_stock -= quantity

        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="manual_reduce",
            quantity=quantity,
            created_by=user_id
        )

        db.add(transaction)

        db.commit()
        db.refresh(inventory)

        # REDIS
        redis_client.publish(
            "inventory.updated",
            {
                "inventory_id": inventory.id,
                "available_stock": inventory.available_stock
            }
        )

        # KAFKA
        event_bus.publish(
            "inventory-events",
            {
                "event": "inventory_reduced",
                "inventory_id": inventory.id,
                "quantity": quantity,
                "user_id": user_id
            }
        )

        # AUDIT
        self.audit.log(
            db=db,
            user_id=user_id,
            action="inventory_reduced",
            entity_type="inventory",
            entity_id=inventory.id,
            metadata={
                "quantity": quantity
            },
            ip=ip
        )

        return inventory