from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_agent import MarketAgent


class AgentVerificationService:

    async def is_valid_agent(
        self,
        db: AsyncSession,
        user_id: str
    ) -> bool:

        result = await db.execute(
            select(MarketAgent).where(
                MarketAgent.user_id == user_id,
                MarketAgent.is_verified_agent == True,
                MarketAgent.status == "approved"
            )
        )

        agent = result.scalar_one_or_none()

        return bool(agent)


agent_verification_service = AgentVerificationService()