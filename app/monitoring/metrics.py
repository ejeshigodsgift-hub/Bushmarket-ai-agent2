from prometheus_client import Counter, Histogram

# Payments
payment_success_total = Counter(
    "payment_success_total",
    "Total successful payments"
)

payment_failed_total = Counter(
    "payment_failed_total",
    "Total failed payments"
)

# Wallets
wallet_topup_total = Counter(
    "wallet_topup_total",
    "Total wallet topups"
)

wallet_withdrawal_total = Counter(
    "wallet_withdrawal_total",
    "Total withdrawals"
)

# Webhooks
webhook_received_total = Counter(
    "webhook_received_total",
    "Total webhooks received"
)

webhook_failed_total = Counter(
    "webhook_failed_total",
    "Total failed webhooks"
)

# Performance
payment_processing_seconds = Histogram(
    "payment_processing_seconds",
    "Payment processing duration"
)