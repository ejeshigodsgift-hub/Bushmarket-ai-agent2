class AgentApplicationEventHandler:

    def __init__(self):
        self.market_admin = MarketAdminService()
        self.agent_service = AgentService()

    async def handle_application_approved(self, db, event):

        user_id = event["user_id"]
        admin_id = event["admin_id"]

        await self.market_admin.approve_agent(db, user_id, admin_id)
        await self.agent_service.approve_agent(db, user_id, admin_id)