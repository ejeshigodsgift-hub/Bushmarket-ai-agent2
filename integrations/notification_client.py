class NotificationClient:

    def send(self, user_id, message):
        print(f"[NOTIFY USER] {user_id}: {message}")

    def broadcast(self, cooperative_id, message):
        print(f"[BROADCAST coop={cooperative_id}] {message}")