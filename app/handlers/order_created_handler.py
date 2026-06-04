class OrderCreatedHandler:

async def handle(self, db, event):

    order_id = event["order_id"]

    print(
        f"[ORDER CREATED] Processing {order_id}"
    )