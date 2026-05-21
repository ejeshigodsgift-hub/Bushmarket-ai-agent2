from services.bulk_order_service import BulkOrderService
from integrations.financial_core import FinancialCoreClient
from events.event_bus import EventBus
from events.event_types import COOP_FUNDED


class ProcurementService:

    def __init__(self):
        self.bulk_service = BulkOrderService()
        self.financial = FinancialCoreClient()
        self.events = EventBus()

    def execute_procurement(self, db, cooperative):

        # 1. verify lifecycle alignment (must be funded)
        if cooperative.status != "funded":
            raise Exception("Cooperative not funded")

        # 2. lock escrow funds
        self.financial.hold_escrow(cooperative.id, cooperative.total_pool)

        # 3. trigger bulk order
        order = self.bulk_service.trigger_bulk_order(
            db=db,
            cooperative=cooperative,
            product_id=cooperative.product_id,
            quantity=cooperative.quantity_target,
            price_per_unit=cooperative.contribution_amount
        )

        self.events.publish(COOP_FUNDED, {
            "cooperative_id": cooperative.id,
            "order_id": order.id
        })

        return order