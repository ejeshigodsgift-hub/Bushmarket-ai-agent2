class InventoryReservedHandler:

async def handle(self, db, event):

    inventory_id = event.get(
        "inventory_id"
    )

    print(
        f"[INVENTORY RESERVED] {inventory_id}"
    )