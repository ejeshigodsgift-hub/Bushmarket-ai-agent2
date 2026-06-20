import uuid

from sqlalchemy.orm import Session

from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.cart import Cart
from app.db.models.cart_item import CartItem

from app.services.inventory_service import InventoryService
from app.services.order_validation_service import (
    OrderValidationService
)
from app.services.audit_service import AuditService

from app.integrations.kafka_client import event_bus
from app.integrations.redis_client import redis_client


class OrderService:

    def __init__(self):

        
        self.validation_service = OrderValidationService()
        self.audit_service = AuditService()

    def create_order(
        self,
        db: Session,
        user_id: str,
        cart: Cart
    ):

        if not cart.items:
            raise Exception("Cart is empty")

        subtotal = 0
        market_fee_total = 0

        order = Order(
            user_id=user_id,
            order_number=str(uuid.uuid4())[:12],
            subtotal_amount=0,
            market_fee_amount=0,
            delivery_fee_amount=0,
            total_amount=0
        )

        db.add(order)
        db.flush()

        for item in cart.items:

            listing = item.listing

            self.validation_service.validate_listing_for_checkout(
                listing,
                item.quantity
            )

            total_price = (
                float(item.unit_price)
                * item.quantity
            )

            market_fee = (
                float(item.market_fee)
                * item.quantity
            )

            subtotal += total_price
            market_fee_total += market_fee

            order_item = OrderItem(
                order_id=order.id,
                listing_id=listing.id,
                product_id=listing.product_id,
                market_id=listing.market_id,
                assigned_agent_id=listing.assigned_agent_id,
                measurement_unit_id=listing.measurement_unit_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                market_fee=market_fee,
                total_price=total_price
            )

            db.add(order_item)

            

        order.subtotal_amount = subtotal
        order.market_fee_amount = market_fee_total
        order.total_amount = subtotal + market_fee_total

        cart.status = "converted"

        db.commit()
        db.refresh(order)

        # Redis cache refresh
        redis_client.delete(f"cart:{user_id}")

        # Kafka event
        event_bus.publish(
            "marketplace.order.created",
            {
                "order_id": order.id,
                "user_id": user_id
            }
        )

        # Audit
        self.audit_service.log(
            db=db,
            user_id=user_id,
            action="create_order",
            entity_type="order",
            entity_id=order.id,
            metadata={
                "total": float(order.total_amount)
            }
        )

        return order