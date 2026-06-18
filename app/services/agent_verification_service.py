from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_permission_service import (
    agent_permission_service
)


class AgentVerificationService:

    async def is_valid_agent(
        self,
        db: AsyncSession,
        user_id: str
    ) -> bool:

        return await agent_permission_service.is_agent(
            db=db,
            user_id=user_id
        )