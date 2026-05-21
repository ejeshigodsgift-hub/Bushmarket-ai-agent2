class DeliveryClient:

    def finalize(self, event):
        print(f"[DELIVERY COMPLETE] {event['cooperative_id']}")