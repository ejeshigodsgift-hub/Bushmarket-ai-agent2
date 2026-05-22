from db.session import SessionLocal
from models.ledger import LedgerEntry

from integrations.event_bus import EventBus
from integrations.payment_gateway import PaystackClient, StripeClient
from integrations.notification_service import NotificationService


class FinancialCoreClient:

    def __init__(self):
        self.db = SessionLocal()
        self.event_bus = EventBus()
        self.paystack = PaystackClient()
        self.stripe = StripeClient()
        self.notify = NotificationService()

    # -----------------------------
    # ESCROW HOLD (PRODUCTION)
    # -----------------------------
    def hold_escrow(self, user_id, cooperative_id, amount):

        ledger = LedgerEntry(
            user_id=user_id,
            cooperative_id=cooperative_id,
            amount=amount,
            type="escrow_hold",
            status="held",
            reference=f"ESC-{user_id}-{cooperative_id}"
        )

        self.db.add(ledger)
        self.db.commit()

        self.event_bus.publish("payment_success", {
            "user_id": user_id,
            "cooperative_id": cooperative_id,
            "amount": amount
        })

        self.notify.push(user_id, "Funds held in escrow successfully.")

        return ledger

    # -----------------------------
    # RELEASE PAYMENT (SUPPLIER)
    # -----------------------------
    def release_payment(self, order_id, supplier_id, amount):

        ledger = LedgerEntry(
            user_id=supplier_id,
            cooperative_id=order_id,
            amount=amount,
            type="release",
            status="released",
            reference=f"REL-{order_id}"
        )

        self.db.add(ledger)
        self.db.commit()

        self.event_bus.publish("bulk_purchase_triggered", {
            "order_id": order_id,
            "supplier_id": supplier_id,
            "amount": amount
        })

        return ledger

    # -----------------------------
    # REFUND SYSTEM
    # -----------------------------
    def refund(self, user_id, amount):

        ledger = LedgerEntry(
            user_id=user_id,
            cooperative_id=None,
            amount=amount,
            type="refund",
            status="refunded",
            reference=f"REF-{user_id}"
        )

        self.db.add(ledger)
        self.db.commit()

        self.notify.push(user_id, "Refund processed successfully.")

        self.event_bus.publish("refund_issued", {
            "user_id": user_id,
            "amount": amount
        })

        return ledger

    # -----------------------------
    # BALANCE CHECK
    # -----------------------------
    def get_coop_balance(self, cooperative_id):

        result = self.db.query(LedgerEntry).filter_by(
            cooperative_id=cooperative_id,
            type="escrow_hold"
        ).all()

        return sum([r.amount for r in result])