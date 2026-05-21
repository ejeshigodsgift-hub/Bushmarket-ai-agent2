class EventBus:

    def publish(self, event_type: str, payload: dict):
        print(f"EVENT: {event_type} -> {payload}")