# =========================================
# FILE: app/services/order_service.py
# =========================================

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.cart import Cart
from app.db.models.checkout import Checkout

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

    # =====================================================
    # PRIMARY FLOW
    # Checkout -> Order
    # =====================================================

    async def create_from_checkout(
        self,
        db: Session,
        checkout: Checkout,
        user_id: str
    ) -> Order:

        if not checkout.items:
            raise Exception("Checkout contains no items")

        subtotal = Decimal("0")
        market_fee_total = Decimal("0")
        delivery_fee_total = Decimal("0")

        order = Order(
            user_id=user_id,
            checkout_id=checkout.id,
            order_number=str(uuid.uuid4())[:12],
            subtotal_amount=Decimal("0"),
            market_fee_amount=Decimal("0"),
            delivery_fee_amount=Decimal("0"),
            total_amount=Decimal("0"),
            status="pending_payment"
        )

        db.add(order)
        db.flush()

        # =====================================
        # CREATE ORDER ITEMS
        # =====================================

        for checkout_item in checkout.items:

            listing = checkout_item.listing

            self.validation_service.validate_listing_for_checkout(
                listing,
                checkout_item.quantity
            )

            quantity = Decimal(str(checkout_item.quantity))

            unit_price = Decimal(
                str(checkout_item.unit_price)
            )

            market_fee_unit = Decimal(
                str(
                    getattr(
                        checkout_item,
                        "market_fee",
                        0
                    )
                )
            )

            delivery_fee_unit = Decimal(
                str(
                    getattr(
                        checkout_item,
                        "delivery_fee",
                        0
                    )
                )
            )

            total_price = unit_price * quantity
            market_fee = market_fee_unit * quantity
            delivery_fee = delivery_fee_unit * quantity

            subtotal += total_price
            market_fee_total += market_fee
            delivery_fee_total += delivery_fee

            order_item = OrderItem(
                order_id=order.id,
                listing_id=listing.id,
                product_id=listing.product_id,
                market_id=listing.market_id,
                measurement_unit_id=listing.measurement_unit_id,
                quantity=int(quantity),
                unit_price=unit_price,
                market_fee=market_fee,
                total_price=total_price
            )

            db.add(order_item)

        # =====================================
        # FINAL TOTALS
        # =====================================

        order.subtotal_amount = subtotal
        order.market_fee_amount = market_fee_total
        order.delivery_fee_amount = delivery_fee_total

        order.total_amount = (
            subtotal
            + market_fee_total
            + delivery_fee_total
        )

        # =====================================
        # LINK CHECKOUT
        # =====================================

        checkout.order_id = order.id
        checkout.status = "converted"

        db.commit()
        db.refresh(order)

        # =====================================
        # CACHE INVALIDATION
        # =====================================

        redis_client.delete(
            f"checkout:{checkout.id}"
        )

        redis_client.delete(
            f"user_checkout:{user_id}"
        )

        # =====================================
        # EVENT
        # =====================================

        event_bus.publish(
            "marketplace.order.created",
            {
                "order_id": order.id,
                "checkout_id": checkout.id,
                "user_id": user_id,
                "total_amount": str(
                    order.total_amount
                )
            }
        )

        # =====================================
        # AUDIT
        # =====================================

        self.audit_service.log(
            db=db,
            user_id=user_id,
            action="create_order",
            entity_type="order",
            entity_id=order.id,
            metadata={
                "checkout_id": checkout.id,
                "total_amount": str(
                    order.total_amount
                )
            }
        )

        return order

    # =====================================================
    # LEGACY FLOW
    # Cart -> Order
    # =====================================================

    def create_order(
        self,
        db: Session,
        user_id: str,
        cart: Cart
    ):

        if not cart.items:
            raise Exception("Cart is empty")

        subtotal = Decimal("0")
        market_fee_total = Decimal("0")

        order = Order(
            user_id=user_id,
            order_number=str(uuid.uuid4())[:12],
            subtotal_amount=Decimal("0"),
            market_fee_amount=Decimal("0"),
            delivery_fee_amount=Decimal("0"),
            total_amount=Decimal("0")
        )

        db.add(order)
        db.flush()

        for item in cart.items:

            listing = item.listing

            self.validation_service.validate_listing_for_checkout(
                listing,
                item.quantity
            )

            unit_price = Decimal(str(item.unit_price))
            market_fee_unit = Decimal(str(item.market_fee))

            total_price = (
                unit_price *
                Decimal(item.quantity)
            )

            market_fee = (
                market_fee_unit *
                Decimal(item.quantity)
            )

            subtotal += total_price
            market_fee_total += market_fee

            order_item = OrderItem(
                order_id=order.id,
                listing_id=listing.id,
                product_id=listing.product_id,
                market_id=listing.market_id,
                measurement_unit_id=listing.measurement_unit_id,
                quantity=item.quantity,
                unit_price=unit_price,
                market_fee=market_fee,
                total_price=total_price
            )

            db.add(order_item)

        order.subtotal_amount = subtotal
        order.market_fee_amount = market_fee_total
        order.total_amount = (
            subtotal +
            market_fee_total
        )

        cart.status = "converted"

        db.commit()
        db.refresh(order)

        redis_client.delete(
            f"cart:{user_id}"
        )

        event_bus.publish(
            "marketplace.order.created",
            {
                "order_id": order.id,
                "user_id": user_id
            }
        )

        self.audit_service.log(
            db=db,
            user_id=user_id,
            action="create_order",
            entity_type="order",
            entity_id=order.id,
            metadata={
                "total": str(
                    order.total_amount
                )
            }
        )

        return order