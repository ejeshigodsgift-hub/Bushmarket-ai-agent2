class NotificationService:

    def push(self, user_id, message):
        print(f"[PUSH] {user_id}: {message}")

    def sms(self, phone, message):
        print(f"[SMS] {phone}: {message}")

    def email(self, email, message):
        print(f"[EMAIL] {email}: {message}")