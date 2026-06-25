from app.handlers.order_created_handler import (
    OrderCreatedHandler
)

from app.handlers.escrow_refund_handler import (
    EscrowRefundHandler
)

from app.events.event_topics import *

from app.handlers.order_payment_completed_handler import (
    OrderPaymentCompletedHandler
)

from app.handlers.inventory_reserved_handler import (
    InventoryReservedHandler
)

from app.handlers.escrow_deposit_handler import (
    EscrowDepositHandler
)

from app.handlers.escrow_release_handler import (
    EscrowReleaseHandler
)

from app.handlers.ledger_posting_handler import (
    LedgerPostingHandler
)

from app.handlers.notification_handler import (
    NotificationHandler
)

from app.handlers.fraud_detection_handler import (
    FraudDetectionHandler
)

from app.consumers.cooperative_partial_vote_approved_consumer import (
    CooperativePartialVoteApprovedConsumer
)


TOPIC_HANDLERS = {

    # ==========================================
    # MARKETPLACE
    # ==========================================
    "marketplace.order.created": [
        OrderCreatedHandler,
        LedgerPostingHandler,
        NotificationHandler,
        FraudDetectionHandler,
    ],


    "order.payment.completed": [
        OrderPaymentCompletedHandler,
    ],


    "notification.sms.send": [
        NotificationHandler,
    ],

    "notification.email.send": [
        NotificationHandler,
    ],

    "notification.push.send": [
        NotificationHandler,
    ],
    # ==========================================
    # INVENTORY
    # ==========================================
    "inventory_reserved": [
        InventoryReservedHandler,
        FraudDetectionHandler,
    ],

    # ==========================================
    # ESCROW
    # ==========================================
    "escrow.deposit": [
        EscrowDepositHandler,
        LedgerPostingHandler,
        
    ],

    "escrow.release": [
        EscrowReleaseHandler,
        LedgerPostingHandler,
        
    ],

    "escrow.refund": [
        EscrowRefundHandler,
        LedgerPostingHandler,
        NotificationHandler,
    ],

    # ==========================================
    # COOPERATIVE PARTIAL PROCUREMENT
    # ==========================================
    "cooperative.partial_vote.approved": [
        CooperativePartialVoteApprovedConsumer,
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
                {
                    "topic": topic,
                    "payload": payload
                }
            )


event_router = EventRouter()