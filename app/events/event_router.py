from app.handlers.order_created_handler import (OrderCreatedHandler)

from app.handlers.inventory_reserved_handler import (InventoryReservedHandler)

from app.handlers.escrow_deposit_handler import (EscrowDepositHandler)

from app.handlers.escrow_release_handler import (EscrowReleaseHandler)

from app.handlers.ledger_posting_handler import (LedgerPostingHandler)

from app.handlers.notification_handler import (NotificationHandler)

from app.handlers.fraud_detection_handler import (FraudDetectionHandler)

TOPIC_HANDLERS = {

"marketplace.order.created": [
    OrderCreatedHandler,
    LedgerPostingHandler,
    NotificationHandler,
    FraudDetectionHandler,
],

"inventory_reserved": [
    InventoryReservedHandler,
    FraudDetectionHandler,
],

"escrow.deposit": [
    EscrowDepositHandler,
    LedgerPostingHandler,
    NotificationHandler,
],

"escrow.release": [
    EscrowReleaseHandler,
    LedgerPostingHandler,
    NotificationHandler,
],

}

class EventRouter:

async def route(
    self,
    db,
    topic: str,
    payload: dict
):

    handlers = TOPIC_HANDLERS.get(
        topic,
        []
    )

    for handler_cls in handlers:

        handler = handler_cls()

        await handler.handle(
            db,
            payload
        )

event_router = EventRouter()