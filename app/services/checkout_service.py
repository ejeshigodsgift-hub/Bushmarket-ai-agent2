import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

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

    # =====================================
    # CREATE CHECKOUT
    # =====================================
    def create_checkout(self, db: Session, user_id: str, cart):

        self.validator.validate_cart(cart)

        now = datetime.now(timezone.utc)

        subtotal = Decimal("0.00")
        fee_total = Decimal("0.00")
        delivery_fee = Decimal("0.00")

        # =====================================
        # CHECK FOR EXISTING EXPIRED CHECKOUT
        # =====================================
        if cart.checkout:
            if cart.checkout.expires_at and cart.checkout.expires_at < now:
                cart.checkout.is_locked = False

        # =====================================
        # COMPUTE EXPIRY
        # =====================================
        expires_at = now + timedelta(
            minutes=getattr(cart.checkout, "expires_in_minutes", 15)
            if cart.checkout else 15
        )

        # =====================================
        # CREATE CHECKOUT
        # =====================================
        checkout = Checkout(
            user_id=user_id,
            cart_id=cart.id,

            subtotal=Decimal("0.00"),
            market_fee_total=Decimal("0.00"),
            delivery_fee=Decimal("0.00"),
            total=Decimal("0.00"),

            # FIX: enforce locking + expiry
            is_locked=True,
            expires_in_minutes=15,
            expires_at=expires_at
        )

        db.add(checkout)
        db.flush()

        # =====================================
        # PROCESS ITEMS
        # =====================================
        for item in cart.items:

            listing = item.listing

            line_total = Decimal(item.quantity) * item.unit_price
            fee = Decimal(item.quantity) * item.market_fee

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

            # convert reservation → checkout lock
            self.inventory.convert_reservation_to_checkout(
                db=db,
                listing_id=listing.id,
                quantity=item.quantity
            )

        # =====================================
        # FINAL TOTALS
        # =====================================
        checkout.subtotal = subtotal
        checkout.market_fee_total = fee_total
        checkout.delivery_fee = delivery_fee
        checkout.total = subtotal + fee_total

        # =====================================
        # LOCK CART
        # =====================================
        cart.status = "checkout_locked"

        db.commit()
        db.refresh(checkout)

        await payment_service.create_payment_intent(
            db=db,
            user_id=user_id,
            amount=checkout.total,
            purpose="checkout_payment",
            reference=checkout.id,
            checkout_id=checkout.id
        )

        # =====================================
        # REDIS TTL (SYNC WITH DB EXPIRY)
        # =====================================
        ttl_seconds = int((expires_at - now).total_seconds())

        redis_client.set(
            f"checkout:{user_id}",
            checkout.id,
            ttl=ttl_seconds
        )

        # =====================================
        # EVENT BUS
        # =====================================
        event_bus.publish(
            "marketplace.checkout.created",
            {
                "checkout_id": checkout.id,
                "user_id": user_id,
                "total": float(checkout.total),
                "expires_at": checkout.expires_at.isoformat()
            }
        )

        # =====================================
        # AUDIT
        # =====================================
        self.audit.log(
            db=db,
            user_id=user_id,
            action="checkout_created",
            entity_type="checkout",
            entity_id=checkout.id,
            metadata={
                "subtotal": float(subtotal),
                "fee": float(fee_total),
                "expires_at": checkout.expires_at.isoformat()
            }
        )

        return checkout