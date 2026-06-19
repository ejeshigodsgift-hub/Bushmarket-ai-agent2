from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from decimal import Decimal
from datetime import datetime, timedelta, timezone

from app.db.models.cart import Cart
from app.db.models.cart_item import CartItem
from app.db.models.market_product_listing import MarketProductListing
from app.db.models.inventory import Inventory

from app.services.audit_service import AuditService
from app.services.cart_validation_service import CartValidationService
from app.services.cart_pricing_service import CartPricingService
from app.services.inventory_service import InventoryService

from app.integrations.redis_client import redis_client
from app.integrations.kafka_client import event_bus


class CartService:

    CART_TTL_MINUTES = 30

    def __init__(self):
        self.audit_service = AuditService()
        self.validation_service = CartValidationService()
        self.pricing_service = CartPricingService()
        self.inventory_service = InventoryService()

    # =========================================
    # GET OR CREATE CART (WITH EXPIRY FIX)
    # =========================================
    def get_or_create_cart(self, db: Session, user_id: str):

        cart = db.query(Cart).filter(
            Cart.user_id == user_id,
            Cart.status == "active"
        ).first()

        now = datetime.now(timezone.utc)

        if cart:

            # refresh expiry on activity
            cart.expires_at = now + timedelta(minutes=self.CART_TTL_MINUTES)

            return cart

        cart = Cart(
            user_id=user_id,
            status="active",
            subtotal_amount=Decimal("0.00"),
            total_market_fee=Decimal("0.00"),
            total_delivery_fee=Decimal("0.00"),
            total_amount=Decimal("0.00"),
            expires_at=now + timedelta(minutes=self.CART_TTL_MINUTES)
        )

        db.add(cart)
        db.commit()
        db.refresh(cart)

        return cart

    # =========================================
    # ADD TO CART (DECIMAL SAFE + NO DRIFT FIX)
    # =========================================
    def add_to_cart(
        self,
        db: Session,
        user_id: str,
        listing_id: str,
        quantity: int,
        ip_address: str
    ):

        try:

            if quantity <= 0:
                raise HTTPException(400, "Quantity must be greater than zero")

            listing = db.query(MarketProductListing).filter(
                MarketProductListing.id == listing_id
            ).first()

            if not listing:
                raise HTTPException(404, "Listing not found")

            self.validation_service.validate_listing_for_cart(listing)

            inventory = db.query(Inventory).filter(
                Inventory.listing_id == listing.id,
                Inventory.is_active == True
            ).with_for_update().first()

            if not inventory:
                raise HTTPException(404, "Inventory not found")

            self.inventory_service.validate_inventory_for_cart(
                inventory=inventory,
                requested_quantity=quantity
            )

            cart = self.get_or_create_cart(db, user_id)

            existing_item = db.query(CartItem).filter(
                CartItem.cart_id == cart.id,
                CartItem.listing_id == listing.id
            ).first()

            final_quantity = quantity

            if existing_item:
                final_quantity += existing_item.quantity

            self.inventory_service.validate_inventory_for_cart(
                inventory=inventory,
                requested_quantity=final_quantity
            )

            # =========================
            # DECIMAL SAFE PRICING
            # =========================
            pricing = self.pricing_service.calculate_item_total(
                quantity=quantity,
                unit_price=listing.unit_price,
                market_fee=listing.market_fee
            )

            if existing_item:

                existing_item.quantity = final_quantity
                existing_item.unit_price = listing.unit_price
                existing_item.market_fee += pricing["market_fee"]
                existing_item.total_price += pricing["total"]

            else:

                item = CartItem(
                    cart_id=cart.id,
                    listing_id=listing.id,
                    product_id=listing.product_id,
                    market_id=listing.market_id,
                    measurement_unit_id=listing.measurement_unit_id,
                    quantity=quantity,
                    unit_price=listing.unit_price,
                    market_fee=pricing["market_fee"],
                    delivery_fee=Decimal("0.00"),
                    total_price=pricing["total"],
                    status="active"
                )

                db.add(item)

            # =========================================
            # FIXED: RECOMPUTE CART TOTALS (NO DRIFT)
            # =========================================
            items = db.query(CartItem).filter(
                CartItem.cart_id == cart.id
            ).all()

            subtotal = Decimal("0.00")
            market_fee = Decimal("0.00")

            for i in items:
                subtotal += (Decimal(i.quantity) * i.unit_price)
                market_fee += i.market_fee

            cart.subtotal_amount = subtotal
            cart.total_market_fee = market_fee
            cart.total_amount = subtotal + market_fee

            # =========================================
            # EXPIRY REFRESH ON ACTIVITY
            # =========================================
            cart.expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=self.CART_TTL_MINUTES
            )

            # inventory reservation stays unchanged
            self.inventory_service.reserve_inventory(
                db=db,
                inventory=inventory,
                quantity=quantity
            )

            db.commit()

            redis_client.publish(
                "cart.updated",
                {
                    "cart_id": cart.id,
                    "user_id": user_id,
                    "listing_id": listing.id
                }
            )

            event_bus.publish(
                "cart-events",
                {
                    "event": "cart_item_added",
                    "cart_id": cart.id,
                    "listing_id": listing.id,
                    "product_id": listing.product_id,
                    "quantity": quantity
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
                    "product_id": listing.product_id,
                    "quantity": quantity,
                    "market_id": listing.market_id
                },
                ip=ip_address
            )

            return existing_item if existing_item else item

        except HTTPException:
            db.rollback()
            raise

        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(500, "Database transaction failed")

        except Exception:
            db.rollback()
            raise HTTPException(500, "Unable to add item to cart")

    # =========================================
    # CHECKOUT PREPARATION (EXPIRY SAFE)
    # =========================================
    def prepare_checkout(self, db: Session, user_id: str):

        cart = self.get_or_create_cart(db, user_id)

        if not cart:
            raise HTTPException(404, "Cart not found")

        if cart.total_amount <= 0:
            raise HTTPException(400, "Cart is empty")

        if cart.expires_at and cart.expires_at < datetime.now(timezone.utc):
            raise HTTPException(400, "Cart expired")

        return {
            "cart_id": cart.id,
            "subtotal": cart.subtotal_amount,
            "market_fee": cart.total_market_fee,
            "delivery_fee": cart.total_delivery_fee,
            "total": cart.total_amount,
            "expires_at": cart.expires_at,
            "status": "ready_for_checkout"
        }