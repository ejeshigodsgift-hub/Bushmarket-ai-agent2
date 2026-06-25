# ==========================================
# MARKETPLACE
# ==========================================
MARKETPLACE_ORDER_CREATED = "marketplace.order.created"
MARKETPLACE_ORDER_CANCELLED = "marketplace.order.cancelled"
MARKETPLACE_ORDER_COMPLETED = "marketplace.order.completed"

# ==========================================
# PAYMENTS
# ==========================================
PAYMENT_RECEIVED = "payment.received"
PAYMENT_FAILED = "payment.failed"
PAYMENT_REFUNDED = "payment.refunded"
ORDER_PAYMENT_COMPLETED = "order.payment.completed"

# ==========================================
# ESCROW
# ==========================================
ESCROW_DEPOSIT = "escrow.deposit"
ESCROW_RELEASE = "escrow.release"
ESCROW_REFUND = "escrow.refund"
ESCROW_DISPUTE_OPENED = "escrow.dispute.opened"
ESCROW_DISPUTE_RESOLVED = "escrow.dispute.resolved"

# ==========================================
# INVENTORY
# ==========================================
INVENTORY_RESERVED = "inventory_reserved"
INVENTORY_LOW_STOCK = "inventory.low_stock"
INVENTORY_OUT_OF_STOCK = "inventory.out_of_stock"

# ==========================================
# LISTINGS
# ==========================================
LISTING_CREATED = "listing.created"
LISTING_APPROVED = "listing.approved"
LISTING_REJECTED = "listing.rejected"

# ==========================================
# AGENTS
# ==========================================
AGENT_APPROVED = "agent.approved"
AGENT_SUSPENDED = "agent.suspended"

# ==========================================
# NOTIFICATIONS
# ==========================================
NOTIFICATION_SMS_SEND = "notification.sms.send"
NOTIFICATION_EMAIL_SEND = "notification.email.send"
NOTIFICATION_PUSH_SEND = "notification.push.send"
NOTIFICATION_DELIVERED = "notification.delivered"
NOTIFICATION_FAILED = "notification.failed"

# ==========================================
# FRAUD
# ==========================================
FRAUD_DETECTED = "fraud.detected"

# ==========================================
# COOPERATIVES
# ==========================================
COOPERATIVE_CREATED = "cooperative.created"
COOPERATIVE_MEMBER_JOINED = "cooperative.member.joined"
COOPERATIVE_PARTIAL_VOTE_APPROVED = (
    "cooperative.partial_vote.approved"
)
COOPERATIVE_PROCUREMENT_COMPLETED = (
    "cooperative.procurement.completed"
)

# ==========================================
# WALLET
# ==========================================
WALLET_CREDITED = "wallet.credited"
WALLET_DEBITED = "wallet.debited"

# ==========================================
# LEDGER
# ==========================================
LEDGER_ENTRY_POSTED = "ledger.entry.posted"