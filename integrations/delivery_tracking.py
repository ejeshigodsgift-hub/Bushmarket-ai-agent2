class DeliveryTracker:

    def create_shipment(self, order_id):
        return {
            "tracking_id": f"TRK-{order_id}",
            "status": "in_transit"
        }

    def update_status(self, tracking_id, status):
        return {
            "tracking_id": tracking_id,
            "status": status
        }