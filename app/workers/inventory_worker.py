# app/workers/inventory_expiry_worker.py

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.db.models.inventory import Inventory
from app.services.inventory_service import InventoryService


inventory_service = InventoryService()


async def process_inventory_expiry():

    async with SessionLocal() as db:

        now = datetime.now(timezone.utc)

        result = await db.execute(
            select(Inventory).where(
                Inventory.reserved_stock > 0,
                Inventory.expires_at <= now
            )
        )

        expired_items = result.scalars().all()

        for inventory in expired_items:

            try:
                quantity = inventory.reserved_stock

                inventory_service.release_reserved_stock(
                    db=db,
                    inventory=inventory,
                    quantity=quantity,
                    user_id="system",
                    ip="ttl_worker"
                )

            except Exception:
                # do not crash worker loop
                continue

        await db.commit()