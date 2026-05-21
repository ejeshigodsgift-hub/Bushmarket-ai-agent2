from collections import defaultdict
import threading


class EventBus:

    def __init__(self):
        # event_type -> list of handlers
        self.subscribers = defaultdict(list)
        self.lock = threading.Lock()

    # -----------------------------
    # SUBSCRIBE HANDLER
    # -----------------------------
    def subscribe(self, event_type: str, handler):
        with self.lock:
            self.subscribers[event_type].append(handler)

    # -----------------------------
    # PUBLISH EVENT
    # -----------------------------
    def publish(self, event_type: str, payload: dict):

        handlers = self.subscribers.get(event_type, [])

        if not handlers:
            print(f"[EVENT BUS] No handlers for {event_type}")
            return

        for handler in handlers:
            try:
                handler(payload)
            except Exception as e:
                print(f"[EVENT ERROR] {event_type}: {str(e)}")