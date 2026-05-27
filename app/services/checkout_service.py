import uuid

from sqlalchemy.orm import Session

from app.db.models.checkout import Checkout
from app.db.models.checkout_item import CheckoutItem

from app.services.checkout_validation_service import CheckoutValidationService
from app.services.inventory_service import InventoryService
from app.services.audit_service import AuditService

from app.integrations.kafka_client import event_bus
from app.integrations.redis_client import redis_client


class CheckoutService:

    def __init__(self):

        self.validator = CheckoutValidationService()
        self.inventory = InventoryService()
        self.audit = AuditService()

    def create_checkout(self, db: Session, user_id: str, cart):

        self.validator.validate_cart(cart)

        subtotal = 0
        fee_total = 0
        delivery_fee = 0

        checkout = Checkout(
            user_id=user_id,
            cart_id=cart.id,
            subtotal=0,
            market_fee_total=0,
            delivery_fee=0,
            total=0
        )

        db.add(checkout)
        db.flush()

        for item in cart.items:

            listing = item.listing

            line_total = item.quantity * float(item.unit_price)
            fee = item.quantity * float(item.market_fee)

            subtotal += line_total
            fee_total += fee

            checkout_item = CheckoutItem(
                checkout_id=checkout.id,
                listing_id=listing.id,
                product_id=listing.product_id,
                market_id=listing.market_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                market_fee=fee,
                total_price=line_total + fee
            )

            db.add(checkout_item)

            # reserve stock (pre-order lock)
            self.inventory.reserve_stock(
                db,
                listing.id,
                item.quantity
            )

        checkout.subtotal = subtotal
        checkout.market_fee_total = fee_total
        checkout.delivery_fee = delivery_fee
        checkout.total = subtotal + fee_total

        cart.status = "checkout_locked"

        db.commit()
        db.refresh(checkout)

        # Redis lock (prevents double checkout)
        redis_client.set(f"checkout:{user_id}", checkout.id, ttl=900)

        # Kafka event
        event_bus.publish(
            "marketplace.checkout.created",
            {
                "checkout_id": checkout.id,
                "user_id": user_id,
                "total": float(checkout.total)
            }
        )

        # Audit
        self.audit.log(
            db=db,
            user_id=user_id,
            action="checkout_created",
            entity_type="checkout",
            entity_id=checkout.id,
            metadata={
                "subtotal": float(subtotal),
                "fee": float(fee_total)
            }
        )

        return checkout