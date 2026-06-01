from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.role import Role
from app.db.models.market_agent import MarketAgent


class AgentPermissionService:

    # ====================================================
    # CORE AGENT VALIDATION
    # ====================================================
    async def is_agent(self, db: AsyncSession, user_id: str) -> bool:

        # STEP 1: must have agent role
        role_result = await db.execute(
            select(Role).where(
                Role.user_id == user_id,
                Role.role == "agent"
            )
        )

        role = role_result.scalar_one_or_none()

        if not role:
            return False

        # STEP 2: must exist in MarketAgent table AND be approved
        agent_result = await db.execute(
            select(MarketAgent).where(
                MarketAgent.user_id == user_id,
                MarketAgent.status == "approved",
                MarketAgent.is_verified_agent.is_(True)
            )
        )

        agent = agent_result.scalar_one_or_none()

        return agent is not None

    # ====================================================
    # STRICT CHECK (RAISES EXCEPTION)
    # ====================================================
    async def require_agent(self, db: AsyncSession, user_id: str) -> None:

        if not await self.is_agent(db, user_id):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=403,
                detail="Agent not approved or inactive"
            )

    # ====================================================
    # CHECK ONLY APPROVAL STATUS (OPTIONAL UTILITY)
    # ====================================================
    async def is_approved_agent(self, db: AsyncSession, user_id: str) -> bool:

        result = await db.execute(
            select(MarketAgent).where(
                MarketAgent.user_id == user_id,
                MarketAgent.status == "approved"
            )
        )

        return result.scalar_one_or_none() is not None

    # ====================================================
    # CHECK VERIFICATION ONLY (OPTIONAL UTILITY)
    # ====================================================
    async def is_verified_agent(self, db: AsyncSession, user_id: str) -> bool:

        result = await db.execute(
            select(MarketAgent).where(
                MarketAgent.user_id == user_id,
                MarketAgent.is_verified_agent.is_(True)
            )
        )

        return result.scalar_one_or_none() is not None


# SINGLETON
agent_permission_service = AgentPermissionService()