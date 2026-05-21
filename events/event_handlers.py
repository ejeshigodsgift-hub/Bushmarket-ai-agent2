from integrations.financial_core import FinancialCoreClient
from integrations.notification_client import NotificationClient
from integrations.ai_client import AIClient
from integrations.cooperative_client import CooperativeClient
from integrations.procurement_client import ProcurementClient
from integrations.delivery_client import DeliveryClient


financial = FinancialCoreClient()
notify = NotificationClient()
ai = AIClient()
coop = CooperativeClient()
procurement = ProcurementClient()
delivery = DeliveryClient()


# -----------------------------
# MEMBER JOINED
# -----------------------------
def handle_member_joined(event):

    coop_id = event["cooperative_id"]
    user_id = event["user_id"]

    notify.send(user_id, "You joined a cooperative successfully.")
    ai.alert(event)


# -----------------------------
# PAYMENT SUCCESS (ESCROW ENTRY)
# -----------------------------
def handle_payment_success(event):

    financial.hold_escrow(
        user_id=event["user_id"],
        cooperative_id=event["cooperative_id"],
        amount=event["amount"]
    )

    notify.send(event["user_id"], "Payment secured in escrow.")


# -----------------------------
# FUNDING MILESTONE
# -----------------------------
def handle_funding_milestone(event):

    ai.alert(event)

    notify.broadcast(
        event["cooperative_id"],
        f"Funding reached {event['percent']}%"
    )


# -----------------------------
# COOPERATIVE FUNDED
# -----------------------------
def handle_cooperative_funded(event):

    coop.update_status(event["cooperative_id"], "funded")

    procurement.trigger_bulk_purchase(event)

    notify.broadcast(
        event["cooperative_id"],
        "🎉 Cooperative fully funded. Preparing bulk purchase."
    )


# -----------------------------
# BULK PURCHASE TRIGGERED
# -----------------------------
def handle_bulk_purchase(event):

    procurement.execute_order(event)

    notify.broadcast(
        event["cooperative_id"],
        "🛒 Bulk purchase initiated."
    )


# -----------------------------
# DELIVERY COMPLETED
# -----------------------------
def handle_delivery_completed(event):

    delivery.finalize(event)

    financial.release_escrow(event["cooperative_id"])

    notify.broadcast(
        event["cooperative_id"],
        "📦 Delivery completed successfully."
    )