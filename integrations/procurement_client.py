class ProcurementClient:

    def trigger_bulk_purchase(self, event):
        print(f"[PROCUREMENT] Triggered for coop {event['cooperative_id']}")

    def execute_order(self, event):
        print(f"[ORDER EXECUTION] Coop {event['cooperative_id']}")