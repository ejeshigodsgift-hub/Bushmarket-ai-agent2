class EventBus:

    def subscribe(self, event_type: str, handler):
        # placeholder for Kafka / Redis / RabbitMQ
        pass

    def publish(self, event_type: str, payload: dict):
        print(f"[EVENT] {event_type}: {payload}")