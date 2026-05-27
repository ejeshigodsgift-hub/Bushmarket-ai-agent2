from sqlalchemy.orm import Session

from app.db.models.inventory import Inventory
from app.db.models.inventory_transaction import InventoryTransaction

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

    # =========================
    # RESERVE STOCK
    # =========================
    def reserve_stock(
        self,
        db: Session,
        inventory_id: str,
        quantity: int,
        user_id: str,
        ip: str
    ):

        inventory = db.query(Inventory).filter(
            Inventory.id == inventory_id
        ).with_for_update().first()

        self.validator.validate_stock(
            inventory,
            quantity
        )

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
                "event": "stock_reserved",
                "inventory_id": inventory.id,
                "quantity": quantity
            }
        )

        # AUDIT
        self.audit.log(
            db=db,
            user_id=user_id,
            action="inventory_reserved",
            entity_type="inventory",
            entity_id=inventory.id,
            metadata={
                "quantity": quantity
            },
            ip=ip
        )

        return inventory

    # =========================
    # CONFIRM SALE
    # =========================
    def confirm_sale(
        self,
        db: Session,
        inventory_id: str,
        quantity: int
    ):

        inventory = db.query(Inventory).filter(
            Inventory.id == inventory_id
        ).with_for_update().first()

        inventory.reserved_stock -= quantity
        inventory.sold_stock += quantity

        db.add(
            InventoryTransaction(
                inventory_id=inventory.id,
                transaction_type="sold",
                quantity=quantity
            )
        )

        db.commit()

        return inventory

    # =========================
    # RELEASE RESERVED STOCK
    # =========================
    def release_reserved_stock(
        self,
        db: Session,
        inventory_id: str,
        quantity: int
    ):

        inventory = db.query(Inventory).filter(
            Inventory.id == inventory_id
        ).with_for_update().first()

        inventory.reserved_stock -= quantity
        inventory.available_stock += quantity

        db.add(
            InventoryTransaction(
                inventory_id=inventory.id,
                transaction_type="release",
                quantity=quantity
            )
        )

        db.commit()

        return inventory