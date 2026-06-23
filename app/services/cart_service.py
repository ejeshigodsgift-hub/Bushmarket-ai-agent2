# from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
    
    async def get_or_create_cart(self,  db: AsyncSession, user_id: str):

        result = await db.execute(
            select(Cart).where(
                Cart.user_id == user_id,
                Cart.status == "active"
            )
        )
        cart = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if cart:
            cart.expires_at = now + timedelta(minutes=self.CART_TTL_MINUTES)
            await db.flush()
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
        await db.commit()
        await db.refresh(cart)

        return cart

    # =========================================
    # ADD TO CART (DECIMAL SAFE + NO DRIFT FIX)
    # =========================================
    async def add_to_cart(
        self,
        db: AsyncSession,
        user_id: str,
        listing_id: str,
        quantity: int,
        ip_address: str
    ):

        try:
            if quantity <= 0:
                raise HTTPException(400,  "Quantity must be greater than zero")

            result = await db.execute(
            select(MarketProductListing).where(
                    MarketProductListing.id == listing_id
                )
            )
            listing =   result.scalar_one_or_none()

            if not listing:
                raise HTTPException(404,  "Listing not found")

          self.validation_service.validate_listing_for_cart(listing)

            inv_result = await db.execute(
                select(Inventory).where(
                    Inventory.listing_id == listing.id,
                    Inventory.is_active == True
                )
            )
            inventory =     inv_result.scalar_one_or_none()

            if not inventory:
                raise HTTPException(404, "Inventory not found")

            self.inventory_service.validate_inventory_for_cart(
                inventory=inventory,
                requested_quantity=quantity
            )

            cart = await self.get_or_create_cart(db, user_id)

            item_result = await db.execute(
                select(CartItem).where(
                    CartItem.cart_id == cart.id,
                    CartItem.listing_id == listing.id
                )
            )
            existing_item = item_result.scalar_one_or_none()

            final_quantity = quantity + (existing_item.quantity if existing_item else 0)

        self.inventory_service.validate_inventory_for_cart(
                inventory=inventory,
            requested_quantity=final_quantity
            )

            pricing = self.pricing_service.calculate_item_total(
                quantity=quantity,
            unit_price=listing.unit_price,
                market_fee=listing.market_fee
            )

            if existing_item:
                existing_item.quantity =   final_quantity
                existing_item.unit_price = listing.unit_price

                pricing = self.pricing_service.calculate_item_total(
                    quantity=final_quantity,
            unit_price=listing.unit_price,
             market_fee=listing.market_fee
                )

                existing_item.market_fee = pricing["market_fee"]
                existing_item.total_price = pricing["total"]

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
                await db.flush()

        # recompute totals (NO DRIFT)
            items_result = await db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id)
            )
            items =   items_result.scalars().all()

            subtotal = Decimal("0.00")
            market_fee = Decimal("0.00")

            for i in items:
                subtotal += Decimal(i.quantity) * i.unit_price
                market_fee += i.market_fee

            cart.subtotal_amount = subtotal
            cart.total_market_fee = market_fee
            cart.total_amount = subtotal + market_fee

            cart.expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=self.CART_TTL_MINUTES
            )

        # inventory reservation MUST be  awaited
            await   self.inventory_service.reserve_stock(
                db=db,
                inventory=inventory,
                quantity=quantity,
                user_id=user_id,
                ip=ip_address
            )

            await db.commit()

           redis_client.publish("cart.updated", {
                "cart_id": cart.id,
                "user_id": user_id,
                "listing_id": listing.id
            })

            event_bus.publish("cart-events", {
                "event": "cart_item_added",
                "cart_id": cart.id,
                "listing_id": listing.id,
                "product_id": listing.product_id,
                "quantity": quantity
            })

            return existing_item if existing_item else item

        except HTTPException:
            await db.rollback()
            raise

        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(500, "Database transaction failed")


        except Exception:
            await db.rollback()
            raise HTTPException(500,   "Unable to add item to cart")




    async def remove_from_cart(
        self,
        db: AsyncSession,
        user_id: str,
        cart_item_id: str,
        ip_address: str
    ):

        try:

            item_result = await db.execute(
                select(CartItem).where(
                    CartItem.id == cart_item_id
                )
            )
            item = item_result.scalar_one_or_none()

            if not item:
                raise HTTPException(404, "Cart item not found")

            cart = item.cart

            if str(cart.user_id) != str(user_id):
                raise HTTPException(403, "Unauthorized cart access")

            listing = item.listing

            inventory_result = await db.execute(
                select(Inventory).where(
                    Inventory.listing_id == listing.id,
                    Inventory.is_active == True
                )
            )
            inventory = inventory_result.scalar_one_or_none()

            if not inventory:
                raise HTTPException(404, "Inventory not found")

            removed_quantity = item.quantity

            await self.inventory_service.release_reserved_stock(
                db=db,
                inventory=inventory,
                quantity=removed_quantity,
                user_id=user_id,
                ip=ip_address
            )

            await db.delete(item)
            await db.flush()

        # recompute totals
            items_result = await db.execute(
                select(CartItem).where(
                    CartItem.cart_id == cart.id
                )
            )
            items = items_result.scalars().all()

            subtotal = Decimal("0.00")
            market_fee = Decimal("0.00")

            for i in items:
                subtotal += Decimal(i.quantity) * i.unit_price
                market_fee += i.market_fee

            cart.subtotal_amount = subtotal
            cart.total_market_fee = market_fee
            cart.total_amount = subtotal + market_fee

            cart.expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=self.CART_TTL_MINUTES
            )

            await db.commit()

            return {
                "message": "Item removed",
                "cart_id": str(cart.id)
            }

        except HTTPException:
            await db.rollback()
            raise

        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(500,   "Database transaction failed")

        except Exception:
            await db.rollback()
            raise HTTPException(500, "Unable to remove item")



    async def update_cart_item_quantity(
        self,
        db: AsyncSession,
        user_id: str,
        cart_item_id: str,
        new_quantity: int,
        ip_address: str
    ):

        try:

            if new_quantity <= 0:
                raise HTTPException(
                    400,
                    "Quantity must be greater than zero"
                )

            item_result = await db.execute(
                select(CartItem).where(
                    CartItem.id == cart_item_id
                )
            )
            item = item_result.scalar_one_or_none()

            if not item:
                raise HTTPException(404, "Cart item not found")

            if str(item.cart.user_id) != str(user_id):
                raise HTTPException(403, "Unauthorized cart access")

            inventory_result = await db.execute(
                select(Inventory).where(
                    Inventory.listing_id == item.listing_id,
                    Inventory.is_active == True
                )
            )
            inventory = inventory_result.scalar_one_or_none()

            if not inventory:
                raise HTTPException(404, "Inventory not found")

            diff = new_quantity - item.quantity

            if diff > 0:
                await self.inventory_service.reserve_stock(
                    db=db,
                    inventory=inventory,
                    quantity=diff,
                    user_id=user_id,
                    ip=ip_address
                )

            elif diff < 0:
                await self.inventory_service.release_reserved_stock(
                    db=db,
                    inventory=inventory,
                    quantity=abs(diff),
                    user_id=user_id,
                    ip=ip_address
                )

        # update quantity
            item.quantity = new_quantity

        # FIX: recalculate fee
            pricing = self.pricing_service.calculate_item_total(
                quantity=new_quantity,
                unit_price=item.unit_price,
             market_fee=item.listing.market_fee
            )

            item.market_fee = pricing["market_fee"]
            item.total_price = pricing["total"]

            cart = item.cart

            items_result = await db.execute(
                select(CartItem).where(
                    CartItem.cart_id == cart.id
                )
            )
            items = items_result.scalars().all()

            subtotal = Decimal("0.00")
            market_fee = Decimal("0.00")

            for i in items:
                subtotal += Decimal(i.quantity) * i.unit_price
                market_fee += i.market_fee

            cart.subtotal_amount = subtotal
            cart.total_market_fee = market_fee
            cart.total_amount = subtotal + market_fee

            cart.expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=self.CART_TTL_MINUTES
            )

            await db.commit()

            return item

        except HTTPException:
            await db.rollback()
            raise

        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(500,  "Database transaction failed")

        except Exception:
            await db.rollback()
            raise HTTPException(
                500,
                "Unable to update cart item quantity"
            )
    # =========================================
    # CHECKOUT PREPARATION (EXPIRY SAFE)
    # =========================================
    async def prepare_checkout(self, db:    AsyncSession, user_id: str):

        result = await db.execute(
            select(Cart).where(
                Cart.user_id == user_id,
                Cart.status == "active"
            )
        )
        cart = result.scalar_one_or_none()

        if not cart:
            raise HTTPException(404, "Cart not found")

        if cart.total_amount <= 0:
            raise HTTPException(400, "Cart is empty")

    # ❗ IMPORTANT: DO NOT refresh expiry  here
        if cart.expires_at and    cart.expires_at <    datetime.now(timezone.utc):
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