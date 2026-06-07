class AILogger:

    async def log_user_message(self, db, user_id, message):
        pass

    async def log_system_action(self, db, user_id, action, data):
        pass


ai_logger = AILogger()