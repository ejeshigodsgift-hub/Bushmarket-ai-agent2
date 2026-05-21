from models.order import CooperativeOrder, OrderStatus
from repositories.order_repo import OrderRepository
from integrations.financial_core import FinancialCoreClient
from events.event_bus import EventBus
from events.event_types import BULK_ORDER_TRIGGERED


class BulkOrderService:

    def __init__(self):
        self.repo = OrderRepository()
        self.financial = FinancialCoreClient()
        self.events = EventBus()

    def trigger_bulk_order(self, db, cooperative, product_id, quantity, price_per_unit):

        total_amount = quantity * price_per_unit

        # ESCROW CHECK (integration with financial_core)
        balance = self.financial.get_coop_balance(cooperative.id)

        if balance < total_amount:
            return self._partial_procurement(db, cooperative, quantity)

        order = CooperativeOrder(
            cooperative_id=cooperative.id,
            product_id=product_id,
            total_quantity=quantity,
            total_amount=total_amount,
            status=OrderStatus.processing
        )

        created = self.repo.create(db, order)

        self.events.publish(BULK_ORDER_TRIGGERED, {
            "cooperative_id": cooperative.id,
            "order_id": created.id
        })

        return created

    # -----------------------------
    # PARTIAL PROCUREMENT SYSTEM
    # -----------------------------
    def _partial_procurement(self, db, cooperative, quantity):

        partial_qty = int(quantity * 0.6)  # fallback logic (configurable)

        order = CooperativeOrder(
            cooperative_id=cooperative.id,
            product_id=cooperative.product_id,
            total_quantity=partial_qty,
            total_amount=0,
            status=OrderStatus.partial
        )

        created = self.repo.create(db, order)

        self.events.publish("partial_procurement", {
            "cooperative_id": cooperative.id,
            "partial_quantity": partial_qty
        })

        return created