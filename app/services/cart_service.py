# =========================================
# FILE: app/services/cart_service.py
# =========================================

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from app.db.models.cart import Cart
from app.db.models.cart_item import CartItem
from app.db.models.market_listing import MarketListing
from app.db.models.inventory import Inventory

from app.services.audit_service import AuditService
from app.services.cart_validation_service import CartValidationService
from app.services.cart_pricing_service import CartPricingService
from app.services.inventory_service import InventoryService

from app.integrations.redis_client import redis_client
from app.integrations.kafka_client import event_bus


class CartService:

    def __init__(self):

        self.audit_service = AuditService()

        self.validation_service = CartValidationService()

        self.pricing_service = CartPricingService()

        self.inventory_service = InventoryService()

    # =========================================
    # GET OR CREATE CART
    # =========================================

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

        cart = Cart(
            user_id=user_id,
            status="active",
            subtotal_amount=0,
            total_market_fee=0,
            total_amount=0
        )

        db.add(cart)
        db.commit()
        db.refresh(cart)

        return cart

    # =========================================
    # ADD TO CART
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

            # =========================================
            # VALIDATE QUANTITY
            # =========================================

            if quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Quantity must be greater than zero"
                )

            # =========================================
            # GET LISTING
            # =========================================

            listing = db.query(MarketListing).filter(
                MarketListing.id == listing_id
            ).first()

            if not listing:
                raise HTTPException(
                    status_code=404,
                    detail="Listing not found"
                )

            # =========================================
            # VALIDATE LISTING
            # =========================================

            self.validation_service.validate_listing_for_cart(
                listing
            )

            # =========================================
            # VALIDATE INVENTORY
            # =========================================

            inventory = db.query(Inventory).filter(
                Inventory.listing_id == listing.id,
                Inventory.is_active == True
            ).with_for_update().first()

            if not inventory:
                raise HTTPException(
                    status_code=404,
                    detail="Inventory not found"
                )

            self.inventory_service.validate_inventory_for_cart(
                inventory=inventory,
                requested_quantity=quantity
            )

            # =========================================
            # GET CART
            # =========================================

            cart = self.get_or_create_cart(
                db=db,
                user_id=user_id
            )

            # =========================================
            # CHECK EXISTING CART ITEM
            # =========================================

            existing_item = db.query(CartItem).filter(
                CartItem.cart_id == cart.id,
                CartItem.listing_id == listing.id
            ).first()

            total_requested_quantity = quantity

            if existing_item:
                total_requested_quantity += existing_item.quantity

            self.inventory_service.validate_inventory_for_cart(
                inventory=inventory,
                requested_quantity=total_requested_quantity
            )

            # =========================================
            # PRICING
            # =========================================

            pricing = self.pricing_service.calculate_item_total(
                quantity=quantity,
                unit_price=listing.unit_price,
                market_fee=listing.market_fee
            )

            # =========================================
            # UPDATE EXISTING ITEM
            # =========================================

            if existing_item:

                existing_item.quantity += quantity

                existing_item.total_price += pricing["total"]

                existing_item.market_fee += pricing["market_fee"]

                existing_item.updated_at = listing.updated_at

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
                    total_price=pricing["total"],
                    status="active"
                )

                db.add(item)

            # =========================================
            # UPDATE CART TOTALS
            # =========================================

            cart.subtotal_amount += pricing["subtotal"]

            cart.total_market_fee += pricing["market_fee"]

            cart.total_amount += pricing["total"]

            # =========================================
            # RESERVE INVENTORY
            # =========================================

            self.inventory_service.reserve_inventory(
                db=db,
                inventory=inventory,
                quantity=quantity
            )

            # =========================================
            # SAVE
            # =========================================

            db.commit()

            # =========================================
            # REDIS EVENT
            # =========================================

            redis_client.publish(
                "cart.updated",
                {
                    "cart_id": cart.id,
                    "user_id": user_id,
                    "listing_id": listing.id
                }
            )

            # =========================================
            # KAFKA EVENT
            # =========================================

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

            # =========================================
            # AUDIT LOG
            # =========================================

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

            if existing_item:
                return existing_item

            return item

        except HTTPException:
            db.rollback()
            raise

        except SQLAlchemyError:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail="Database transaction failed"
            )

        except Exception:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail="Unable to add item to cart"
            )