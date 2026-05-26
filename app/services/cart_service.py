from sqlalchemy.orm import Session

from app.db.models.cart import Cart
from app.db.models.cart_item import CartItem
from app.db.models.market_listing import MarketListing

from app.services.audit_service import AuditService
from app.services.cart_validation_service import CartValidationService
from app.services.cart_pricing_service import CartPricingService

from app.integrations.redis_client import redis_client
from app.integrations.kafka_client import event_bus


class CartService:

    def __init__(self):

        self.audit_service = AuditService()

        self.validation_service = CartValidationService()

        self.pricing_service = CartPricingService()

    # =========================
    # GET OR CREATE CART
    # =========================

    def get_or_create_cart(
        self,
        db: Session,
        user_id: str
    ):

        cart = db.query(Cart).filter(
            Cart.user_id == user_id,
            Cart.status == "active"
        ).first()

        if cart:
            return cart

        cart = Cart(user_id=user_id)

        db.add(cart)
        db.commit()
        db.refresh(cart)

        return cart

    # =========================
    # ADD TO CART
    # =========================

    def add_to_cart(
        self,
        db: Session,
        user_id: str,
        listing_id: str,
        quantity: int,
        ip_address: str
    ):

        listing = db.query(MarketListing).filter(
            MarketListing.id == listing_id
        ).first()

        self.validation_service.validate_listing_for_cart(
            listing
        )

        cart = self.get_or_create_cart(
            db,
            user_id
        )

        pricing = self.pricing_service.calculate_item_total(
            quantity=quantity,
            unit_price=listing.unit_price,
            market_fee=listing.market_fee
        )

        item = CartItem(
            cart_id=cart.id,
            listing_id=listing.id,
            product_id=listing.product_id,
            market_id=listing.market_id,
            measurement_unit_id=listing.measurement_unit_id,
            quantity=quantity,
            unit_price=listing.unit_price,
            market_fee=listing.market_fee,
            total_price=pricing["total"]
        )

        db.add(item)

        cart.subtotal_amount += pricing["subtotal"]
        cart.total_market_fee += pricing["market_fee"]
        cart.total_amount += pricing["total"]

        db.commit()

        redis_client.publish(
            "cart.updated",
            {
                "cart_id": cart.id,
                "user_id": user_id
            }
        )

        event_bus.publish(
            "cart-events",
            {
                "event": "cart_item_added",
                "cart_id": cart.id,
                "listing_id": listing.id
            }
        )

        self.audit_service.log(
            db=db,
            user_id=user_id,
            action="cart_item_added",
            entity_type="cart",
            entity_id=cart.id,
            metadata={
                "listing_id": listing.id,
                "quantity": quantity
            },
            ip=ip_address
        )

        return item