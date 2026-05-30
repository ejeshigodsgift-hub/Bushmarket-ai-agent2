from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.role import Role
from app.db.models.market_agent import MarketAgent


class AgentPermissionService:

    async def is_agent(self, db: AsyncSession, user_id: str) -> bool:

        # MUST have role = agent
        role_result = await db.execute(
            select(Role).where(
                Role.user_id == user_id,
                Role.role == "agent"
            )
        )
        has_agent_role = role_result.scalar_one_or_none()

        if not has_agent_role:
            return False

        # MUST be approved in MarketAgent table
        agent_result = await db.execute(
            select(MarketAgent).where(
                MarketAgent.user_id == user_id,
                MarketAgent.status == "approved",
                MarketAgent.is_verified_agent == True
            )
        )

        approved_agent = agent_result.scalar_one_or_none()

        return approved_agent is not None


agent_permission_service = AgentPermissionService()